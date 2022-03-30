# This file contains the base Class definition for the Waters Shortage Datasets
import abc
import pandas as pd
import geopandas as gpd

from typing import List, Tuple
from shapely.geometry import Polygon, MultiPolygon, MultiPoint
from shapely.ops import voronoi_diagram


class BaseWsDataset(abc.ABC):
    @abc.abstractmethod
    def preprocess_map_df(self, features_to_keep: List[str]):
        pass


class WsGeoDataset(BaseWsDataset):
    """This is the parent class for the loading, ETL and export of the datasets used in the Water Shortage analysis

    """
    def __init__(self, input_geofiles: List[str], input_datafile: str = None, input_datafile_format: str = "csv",
                 merging_keys: List[str] = None, sjv_shapefile: str = "../assets/inputs/common/plss_subbasin.geojson",
                 ca_shapefile= "../assets/inputs/common/ca_county_boundaries/CA_Counties_TIGER2016.shp"):
        """Initialization of the dataset class.

        :param input_geofiles: list of of geospatial files to vertically concatenate. The geospatial datasets must
        have the same columns to be concatenated horizontally.
        :param input_datafile: if the data are not included in the shapefile together with the map data, provide the
        path to the file containing the map data
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :param merging_keys: if the data and map are separated in different files, the keys used to merge the map units
        with their corresponding data. The first string in the list is the name of the key  of the shapefile dataset and
        the second string the name of the key in the data dataset
        :param sjv_shapefile: the path to the shapefile containing the TRS data for the San Joaquin Valley
        """
        # map_df is a GeoPandas dataframe containing geospatial land areas together with the data.
        # This dataframe can be use to display features of land areas
        self.map_df = gpd.GeoDataFrame()
        # data_df is an optional Pandas dataframe containing additional data describing the land areas in map_df
        self.data_df = pd.DataFrame()
        # output_df is the Pandas dataframe containing the processed data by Township-Range and year and without the
        # geospatial data. It is meant to be exported in a file for the downstream analysis.
        self.output_df = pd.DataFrame()
        self.__merging_keys = merging_keys

        if input_geofiles:
            self.map_df = self._read_geospatial_file(input_geofiles[0])
            if len(input_geofiles) > 1:
                for input_shapefile in input_geofiles[1:]:
                    self.map_df = pd.concat([self.map_df, self._read_geospatial_file(input_shapefile)], axis=0)
                self.map_df.reset_index(inplace=True, drop=True)

        if input_datafile:
            self.data_df = self._read_input_datafile(input_datafile, input_datafile_format)

        self.sjv_township_range_df, self.sjv_boundaries = self._preprocess_sjv_shapefile(sjv_shapefile)
        self.ca_counties_df, self.ca_boundaries = self._preprocess_ca_shapefile(ca_shapefile)

    def _read_geospatial_file(self, filename: str):
        """Read a Geospatial dataframe and set the projection as WGS84 Latitude/Longitude ("EPSG:4326").

        :param filename: the geospatial fle
        :return: the GeoPandas Dataframe with projection set to EPSG:4326
        """
        return gpd.read_file(filename).to_crs(epsg=4326)

    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        data_df = None
        if input_datafile_format == "csv":
            data_df = pd.read_csv(input_datafile)
        elif input_datafile_format in {"xls", "xlsx"}:
            data_df = pd.read_excel(input_datafile)
        return data_df

    def _close_holes(self, poly: Polygon) -> Polygon:
        """This function closes polygon holes by limitation to the exterior ring.
        I.e. if there are any empty space inside a Polygon (e.g. O) it will only keep the coordinates
        of the external boundaries of the Polygon as the new Polygon shape (e.g. █).
        :param poly: Input shapely Polygon to close
        :return: the closed Polygon
        """
        if poly.interiors:
            return Polygon(list(poly.exterior.coords))
        else:
            return poly

    def _square_township_shapes(self, shape) -> Polygon:
        """This function returns a square polygon encapsulating all the polygons making a Township. This function g
        reatly simplifies the Townships shapes as full square compare to the original shapes.

        :param shape: Input shapely Polygon or Multipolygon to close
        :return: the encapsulating closed Polygon
        """
        if isinstance(shape, MultiPolygon):
            # Extract all the points from the MultiPolygon
            points = []
            for polygon in shape.geoms:
                points.extend(polygon.exterior.coords[:-1])
            # Compute the convex hull of all the points to get the outer boundary of the shape
            shape = MultiPoint(points).convex_hull
        # Compute the square Polygon encapsulating the shape
        bounding_polygon = Polygon([(shape.bounds[0], shape.bounds[1]),
                                    (shape.bounds[0], shape.bounds[3]),
                                    (shape.bounds[2], shape.bounds[3]),
                                    (shape.bounds[2], shape.bounds[1])])
        return bounding_polygon

    def _preprocess_sjv_shapefile(self, sjv_shapefile: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """This function loads the geojson file containing the Township-Range Range Section land survey polygons
        for the San Joaquin Valley.

        :param sjv_shapefile: the path to the shapefile containing the TRS data for the San Joaquin Valley
        :return: a tuple containing the Township-Range polygons of the San Joaquin Valley and the boundary Polygon of the
        San Joaquin Valley
        """
        sjv_plss_df = gpd.read_file(sjv_shapefile)
        # Combine the map units at the Township-Range level
        sjv_township_range_df = sjv_plss_df.dissolve(by='TownshipRange').reset_index()
        # Keep only the 'TownshipRange' and 'geometry' columns
        sjv_township_range_df = sjv_township_range_df[["TownshipRange", "geometry"]]
        sjv_township_range_df.rename(columns={"TownshipRange": "TOWNSHIP_RANGE"}, inplace=True)
        # Simplify the Township shapes to squares
        sjv_township_range_df.geometry = sjv_township_range_df.geometry.apply(lambda p: self._square_township_shapes(p))

        # Create an artificial column with a unique value to merge all the Polygons together
        sjv_polygon = sjv_township_range_df.copy()
        sjv_polygon["merge"] = 0
        sjv_polygon = sjv_polygon.dissolve(by="merge")
        # Fill in any potential holes within the shape. This is important when clipping the San Joaquin Valley
        # polygon over a dataset containing data for the entire state of California. Otherwise it would also clip
        # out data within those holes
        sjv_polygon.geometry = sjv_polygon.geometry.apply(lambda p: self._close_holes(p))
        return sjv_township_range_df, sjv_polygon

    def _preprocess_ca_shapefile(self, ca_shapefile: str) -> gpd.GeoDataFrame:
        """This function loads the geojson file of California counties and returns a geometry of the California state
        boundaries.

        :param ca_shapefile: the path to the shapefile containing the California counties polygons
        :return: A Sahpely Polygon of the California boundaries
        """
        ca_geodf = gpd.read_file(ca_shapefile).to_crs(epsg=4326)
        ca_counties = ca_geodf[["NAME", "geometry"]].copy()
        ca_counties.rename(columns={"NAME": "COUNTY"}, inplace=True)
        # Create an artificial column with a unique value to merge all the Polygons together
        ca_geodf["merge"] = 0
        ca_boundaries = ca_geodf.dissolve(by="merge")
        return ca_counties, ca_boundaries

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function should be used in child classes to perform dataset specific pre-processing of the map dataset.

        :param features_to_keep: the list of features (columns) to keep
        """
        pass

    def merge_map_with_data(self, how: str = "left", dropna: bool = False):
        """This function merges the data dataset into the map dataframe, updates the class' map_df GeoDataFrame and
        drops the map and data keys from the final map dataset.The result is saved in the self.map_df variable.

        :param how: how to merge the data (e.g. "left", "right", "inner").
        :param dropna: whether to drop rows with missing values in the data dataset.
        """
        if self.data_df is not None:
            self.map_df = self.map_df.merge(self.data_df, how=how, left_on=self.__merging_keys[0],
                                            right_on=self.__merging_keys[1])
            self.map_df.drop(self.__merging_keys, axis=1, inplace=True)
        if dropna:
            self.map_df.dropna(inplace=True)

    def fill_townships_with_no_data(self, feature_to_fill: str):
        """Some Township-Ranges in some datasets have no data. This function assigns the "X" "Unclassified" value to
        these Township-Ranges for all the years where they have no data

        :param feature_to_fill: the feature name resulting from ETL, which must be filled with missing data (e.g.
        "CROP_TYPE")."""
        all_townships = set(self.sjv_township_range_df["TOWNSHIP_RANGE"].unique())
        for year in self.map_df["YEAR"].unique():
            year_df = self.map_df[self.map_df["YEAR"] == year]
            missing_townships = all_townships - set(year_df["TOWNSHIP_RANGE"].unique())
            missing_townships_df = self.sjv_township_range_df[self.sjv_township_range_df["TOWNSHIP_RANGE"].isin(
                missing_townships)].copy()
            missing_townships_df["YEAR"] = year
            missing_townships_df[feature_to_fill] = "X"
            self.map_df = pd.concat([self.map_df, missing_townships_df], axis=0)

    def keep_only_sjv_data(self):
        """This function keeps only the map_df data for the San Joaquin Valley and cut the map units by Township-Range.
        Refer to the provided documentation "Overlaying San Joaquin Valley Township-Range Boundaries"
        in ../doc/etl/township_overlay.md. The operation is done independently for every year in the dataset. The result
        is saved in the self.map_df variable.
        """
        self.map_df = gpd.clip(self.map_df, self.sjv_boundaries.geometry[0])
        self.map_df.reset_index(inplace=True, drop=True)

    def overlay_township_boundries(self):
        """This function keeps only the map data for the San Joaquin Valley and cut the map units by Township-Range.
        Refer to the provided documentation "Overlaying San Joaquin Valley Township-Range Boundaries"
        in ../doc/etl/township_overlay.md. The operation is done independently for every year in the dataset. The result
        is saved in the self.map_df variable.
        """
        self.keep_only_sjv_data()
        for i, year in enumerate(self.map_df["YEAR"].unique()):
            yearly_map_df = self.map_df[self.map_df["YEAR"] == year]
            # Overlay the townships boundaries on the map data units to cut and explode them based on the townships
            map_data_by_township_df = gpd.overlay(yearly_map_df, self.sjv_township_range_df, how='identity',
                                                  keep_geom_type=True)
            if i == 0:
                new_map_df = map_data_by_township_df
            else:
                new_map_df = pd.concat([new_map_df, map_data_by_township_df], axis=0)
        new_map_df.reset_index(inplace=True, drop=True)
        self.map_df = new_map_df

    def _compute_areas(self, feature_name: str):
        """This function computes the surface area of the polygons in the GeoPandas dataframe and adds
        a feature called AREA. The result is saved in the self.map_df variable.

        :param feature_name: the name of the original feature to use to compute the values for each new features
        """
        if "TOWNSHIP_RANGE" not in self.map_df.columns:
            self.overlay_township_boundries()
        # Merge rows by TOWNSHIP , YEAR and feature_name
        self.map_df = self.map_df.dissolve(by=["TOWNSHIP_RANGE", "YEAR", feature_name]).reset_index()
        # Compute the area percentage of the feature in each TOWNSHIP for each year
        self.map_df.set_crs("epsg:4326")
        self.map_df["AREA"] = self.map_df.geometry.area
        self.map_df["AREA_PCT"] = self.map_df[["TOWNSHIP_RANGE", "YEAR", "AREA"]].groupby(["TOWNSHIP_RANGE", "YEAR"])["AREA"].\
            apply(lambda x:x/x.sum())
        self.map_df.drop(columns=["AREA"], inplace=True)

    def compute_areas_from_points(self, boundary: str = "ca"):
        """This function takes geospatial points data (e.g. precipitation recorded in one location), and computes year
        by year a Voronoi Diagram of the the Thiessen Polygons to construct the geospatial area data from the points.
        The transformation is done year by year as measurements might not be performed at the exact same location from
        year to year.

        :param voronoi_envelope: the envelope or boundary to use to compute the Voronoi Diagram."""
        new_map_df = gpd.GeoDataFrame()
        if boundary == "svj":
            envelope = self.sjv_boundaries.geometry[0]
        else:
            envelope = self.ca_boundaries.geometry[0]
        for year in self.map_df["YEAR"].unique():
            year_df = self.map_df[self.map_df["YEAR"] == year].copy()
            # Keep the original points for display
            year_df["points"] = year_df["geometry"].copy()
            # Computes the Thiessen Polygon for each point
            voronoi_regions = voronoi_diagram(MultiPoint(list(year_df.geometry)), envelope=envelope)
            voronoi_regions_df = gpd.GeoDataFrame(geometry=list(voronoi_regions.geoms), crs="epsg:4326")
            # The Thiessen Polygon are not returned in a list in the same order than the points
            # So we use SJOIN the merge the Voronoi shapes with the corresponding points and data in order for the
            # shape to match the data
            voronoi_regions_df = voronoi_regions_df.sjoin(year_df)
            # Clip the shapes within the boundaries
            voronoi_regions_df = gpd.clip(voronoi_regions_df, envelope)
            new_map_df = pd.concat([new_map_df, voronoi_regions_df], axis=0)
        self.map_df = new_map_df
        if "index_right" in list(self.map_df.columns):
            self.map_df.drop(columns=["index_right"], inplace=True)

    def return_yearly_normalized_township_feature(self, feature_name: str, normalize_method: str = "mean"):
        """This function returns a dataframe with the feature values normalized by the "YEAR" column.

        :param feature_name: the name of the feature to normalize
        :return: a GeoDataFrame with an additional normalized feature column
        """
        normalized_df = gpd.GeoDataFrame()
        for year in self.map_df["YEAR"].unique():
            year_df = self.map_df[self.map_df["YEAR"] == year].copy()
            if normalize_method == "minmax":
                year_df[f"{feature_name}_NORMALIZED"] = (year_df[feature_name] - year_df[feature_name].mean()) / \
                                                        (year_df[feature_name].max() - year_df[feature_name].min())
            elif normalize_method == "std":
                year_df[f"{feature_name}_NORMALIZED"] = (year_df[feature_name] - year_df[feature_name].min()) / \
                                                        year_df[feature_name].std()
            else:
                year_df[f"{feature_name}_NORMALIZED"] = year_df[feature_name] / year_df[feature_name].mean()
            normalized_df = pd.concat([normalized_df, year_df], axis=0)
        return normalized_df

    def aggregate_points_by_township(self, feature_name: str, aggfunc: str = "mean"):
        """This function keeps only the map_df data for the San Joaquin Valley and merges the points identified by
        their latitude and longitude by TOWNSHIP and YEAR, and use the aggfunc on the feature_name to compute the value
        for the Township.

        :param feature_name: the name of the feature to use to compute the values for each Township-Range
        :param aggfunc: the function to use to aggregate the values per Township-Range"""
        self.keep_only_sjv_data()
        # group datapoints by Townships based on longitude/latitude
        self.map_df = self.map_df.sjoin(self.sjv_township_range_df)
        if "COUNTY" in list(self.map_df.columns):
            self.map_df.drop(columns=["COUNTY"], inplace=True)
        # Group data points with multiple measurements in some years and get the average of feature_name
        self.map_df = self.map_df.dissolve(by=["TOWNSHIP_RANGE", "YEAR"], aggfunc=aggfunc).reset_index()
        self.map_df.drop(columns=["index_right"], inplace=True)

    def aggregate_feature_at_township_level(self, group_by_features: List[str], feature_to_aggregate_on: str,
                                          aggfunc: str = "mean"):
        """This function essentially computes the mean of all values in a Township for each year

        :param feature_name: the name of the original feature to use to compute the values for each new features
        :param feature_prefix: the prefix to add to feature names (e.g. "CROPS" for the Crops dataset features)
        """
        features_to_keep = group_by_features.copy()
        features_to_keep.append(feature_to_aggregate_on)
        if "geometry" not in group_by_features:
            features_to_keep.append("geometry")
        new_map_df = gpd.GeoDataFrame()
        for year in self.map_df["YEAR"].unique():
            year_df = self.map_df[self.map_df["YEAR"] == year].copy()
            year_df = year_df[features_to_keep].dissolve(by=group_by_features, aggfunc=aggfunc).reset_index()
            new_map_df = pd.concat([new_map_df, year_df], axis=0)
        self.map_df = new_map_df

    def prepare_output_from_map_df(self, unwanted_features: List[str] = []):
        """This functions, prepares the map_df Geospastial Dataframe to be written in the output file.
        At the minimum, it removes the geospatial "geometry feature".

        :param unwanted_features: additional list of features to drop."""
        self.output_df = self.map_df.copy()
        if (not unwanted_features) or ("geometry" not in unwanted_features):
            self.output_df.drop(columns=["geometry"], errors="ignore", inplace=True)
        if unwanted_features:
            self.output_df.drop(columns=unwanted_features, errors="ignore", inplace=True)

    def pivot_township_categorical_feature_for_output(self, feature_name: str, feature_prefix: str = ""):
        """This function prepares the output_df dataframe by pivoting the geospatial dataframe, using the values in the
        feature_name parameter as the new feature columns and the land surface percentage the feature occupies in the
        Township-Range as the cell values. E.g. if a Township-Range for a specific year, has 2 land areas, one
        classified as 'A' covering 75% of the Township-Range land and one classified as 'B' covering 25% of the
        Township-Range range, these two rows will transformed as 1 row for the Township-Range but with 2 features A
        with value 75% and feature B with value 25%. The result is saved in the self.output_df variable.

        :param feature_name: the name of the original feature to use to compute the values for each new features
        :param feature_prefix: the prefix to add to feature names (e.g. "CROPS" for the Crops dataset features)
        """
        self._compute_areas(feature_name)
        # Get the land surface used for each feature class
        township_features_df = pd.pivot_table(self.map_df[["TOWNSHIP_RANGE", "YEAR", "AREA_PCT", feature_name]],
                                              index=["TOWNSHIP_RANGE", "YEAR"], columns=[feature_name],
                                              values="AREA_PCT").fillna(0)
        # Rename columns (except "TOWNSHIP_RANGE" and "YEAR") by adding the feature_prefix, replacing spaces by underscores
        # and transform to uppercase
        township_features_df.columns = [
            f"{feature_prefix.replace(' ', '_').strip('_').upper()}_{c.upper().replace(' ', '_')}"
            if c not in {"TOWNSHIP_RANGE", "YEAR"} else c for c in township_features_df.columns]
        township_features_df.reset_index(inplace=True)
        # Merge the townships with their new features
        self.output_df = self.sjv_township_range_df.dissolve(by="TOWNSHIP_RANGE").reset_index().\
            merge(township_features_df, how="right", left_on="TOWNSHIP_RANGE", right_on="TOWNSHIP_RANGE")

    def drop_features(self, drop_rate: float = 0.0, unwanted_features: List[str] = []):
        """This function removes features (columns) from the self.output_df dataset in two ways. 1) it drops the
        features which cover a smaller land surface percentage of every Township-Range for any given year. 2) it drops
        unwanted features (e.g. the "Urban" class from the crops dataset).

        :param drop_rate: any feature which does not appear more that the drop_rate in any of the Township-Range for
        every year will be dropped. This is used to drop features which cover a very small amount of land surface in
        all the Township-Range. Warning: by dropping feature columns, the sum of the feature percentage in impacted
        Township-Range will not sum to 100%.
        :param unwanted_features: the list of features to drop.
        """
        self.output_df.drop(columns=["geometry"], errors="ignore", inplace=True)
        # Drop features which cover a very small amount of land surface.
        for feature in self.output_df.columns:
            if feature not in {"TOWNSHIP_RANGE", "YEAR"} and self.output_df[feature].max() < drop_rate:
                self.output_df.drop(columns=[feature], inplace=True)
        if unwanted_features:
            self.output_df.drop(columns=unwanted_features, errors="ignore", inplace=True)

    def output_dataset_to_csv(self, output_filename: str):
        """This function writes the self.output_df dataframe into a CSV file.

        :param output_filename: the name of the file with the relative path
        """
        if not self.output_df.empty:
            self.output_df.to_csv(output_filename, index=False)
