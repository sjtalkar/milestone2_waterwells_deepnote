import os
import numpy as np
import pandas as pd
import geopandas as gpd

from datetime import datetime
from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import download_well_completion_datasets


class WellCompletionReportsDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_datafile: str = "../assets/inputs/wellcompletion/wellcompletion.csv",
                 elevation_datadir: str = "../assets/inputs/wellcompletion/elevation_data/",
                 ):
        try:
            self._load_local_datasets(input_datafile, elevation_datadir)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_datafile, elevation_datadir)
            self._load_local_datasets(input_datafile, elevation_datadir)

    def _load_local_datasets(self, input_datafile: str, elevation_datadir: str):
        """This function loads the datasets from the local file system

        :param input_datafile: the path to the well completion reports dataset
        :param elevation_datadir: the path to the elevation data directory
        """
        print("Loading local datasets. Please wait...")
        WsGeoDataset.__init__(self, input_geofiles=[], input_datafile="")
        self.elevation_df = self._get_missing_elevation(elevation_datadir)
        wcr_df = self._load_wcr_data(wcr_datafile=input_datafile)
        self.map_df = gpd.GeoDataFrame(
            wcr_df,
            geometry=gpd.points_from_xy(
                wcr_df.LONGITUDE,
                wcr_df.LATITUDE
            ))
        # Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs("epsg:4326")
        print("Loading of datasets complete.")

    def _download_datasets(self, input_datafile: str, elevation_datadir: str):
        """This function downloads the datasets from the web

        :param input_datafile: the path where to store the well completion reports dataset
        :param elevation_datadir: the path where to store the elevation data
        """
        print("Data not found locally.")
        download_well_completion_datasets(input_datafile, elevation_datadir)
        print("Downloads complete.")
        
    def _load_wcr_data(self, wcr_datafile: str):
        # We set the type to avoid pandas warning on some columns with mixed types
        wcr_df = pd.read_csv(wcr_datafile,
                             dtype={"": int,
                                    "DECIMALLATITUDE": str,
                                    "WORKFLOWSTATUS": str,
                                    "LLACCURACY": str,
                                    "PERMITDATE": str,
                                    "PUMPTESTLENGTH": float,
                                    "SECTION": str,
                                    "REGIONOFFICE": str,
                                    "DRILLINGMETHOD": str,
                                    "OTHEROBSERVATIONS": str,
                                    "WELLYIELDUNITOFMEASURE": str,
                                    "WELLLOCATION": str,
                                    "PERMITNUMBER": str,
                                    "TOTALDRAWDOWN": float,
                                    "VERTICALDATUM": str,
                                    "BOTTOMOFPERFORATEDINTERVAL": float,
                                    "GROUNDSURFACEELEVATION": float,
                                    "STATICWATERLEVEL": float,
                                    "RECORDTYPE": str,
                                    "DRILLERLICENSENUMBER": str,
                                    "FLUID": str,
                                    "TESTTYPE": str,
                                    "APN": str,
                                    "PLANNEDUSEFORMERUSE": str,
                                    "LOCALPERMITAGENCY": str,
                                    "TOPOFPERFORATEDINTERVAL": float,
                                    "WCRNUMBER": str,
                                    "TOTALDRILLDEPTH": float,
                                    "LEGACYLOGNUMBER": str,
                                    "ELEVATIONDETERMINATIONMETHOD": str,
                                    "ELEVATIONACCURACY": str,
                                    "DECIMALLONGITUDE": str,
                                    "METHODOFDETERMINATIONLL": str,
                                    "HORIZONTALDATUM": str,
                                    "TOWNSHIP": str,
                                    "DATEWORKENDED": str,
                                    "CITY": str,
                                    "TOTALCOMPLETEDDEPTH": float,
                                    "OWNERASSIGNEDWELLNUMBER": str,
                                    "COUNTYNAME": str,
                                    "RANGE": str,
                                    "BASELINEMERIDIAN": str,
                                    "RECEIVEDDATE": str,
                                    "DRILLERNAME": str,
                                    "WELLYIELD": float,
                                    "_id": int,
                                    "CASINGDIAMETER": float})

        # There are latitudes and longitudes that are corrupt : 37/41/11.82/
        wcr_df = wcr_df[~wcr_df.DECIMALLATITUDE.str.contains(r"/", na=False)].copy()
        wcr_df = wcr_df[~wcr_df.DECIMALLONGITUDE.str.contains(r"/", na=False)].copy()
        wcr_df["DECIMALLATITUDE"] = wcr_df.DECIMALLATITUDE.astype("float")
        wcr_df["DECIMALLONGITUDE"] = wcr_df.DECIMALLONGITUDE.astype("float")
        # Correct incorrectly signed logitude and latiude Example :   120.54483 Longitude
        wcr_df["DECIMALLONGITUDE"] = np.where(wcr_df["DECIMALLONGITUDE"] > 0, -wcr_df["DECIMALLONGITUDE"],
                                              wcr_df["DECIMALLONGITUDE"])
        wcr_df["DECIMALLATITUDE"] = np.where(wcr_df["DECIMALLATITUDE"] < 0, -wcr_df["DECIMALLATITUDE"],
                                             wcr_df["DECIMALLATITUDE"])
        # About 5% of the dataframe has either latitude or longitude missing, we drop these
        wcr_df.dropna(subset=["DECIMALLATITUDE", "DECIMALLONGITUDE"], inplace=True)
        # Pick data of interest
        wcr_df = wcr_df[
            ["DECIMALLATITUDE", "DECIMALLONGITUDE", "SECTION", "WELLLOCATION", "COUNTYNAME",
             "STATICWATERLEVEL", "BOTTOMOFPERFORATEDINTERVAL", "TOPOFPERFORATEDINTERVAL", "GROUNDSURFACEELEVATION",
             "RECORDTYPE", "PLANNEDUSEFORMERUSE", "WCRNUMBER", "TOTALDRILLDEPTH", "TOTALCOMPLETEDDEPTH",
             "DATEWORKENDED", "WELLYIELD", "CASINGDIAMETER", "TOTALDRAWDOWN", "WELLYIELDUNITOFMEASURE"]]
        wcr_df.rename(columns={"DECIMALLATITUDE": "LATITUDE", "DECIMALLONGITUDE": "LONGITUDE", 
                               "PLANNEDUSEFORMERUSE": "USE", "COUNTYNAME": "COUNTY"}, inplace=True)
        return wcr_df

    def _get_missing_elevation(self, elevation_datadir: str):
        """This function reads the elevation data and returns a dataframe with the missing elevation data.

        :param elevation_datadir: the directory of the elevation data
        :return: the dataframe with the missing elevation data
        """
        elevation_file_list = os.listdir(elevation_datadir)
        elevation_df = pd.DataFrame()
        for file_name in elevation_file_list:
            lat_long_elev_df = pd.read_csv(os.path.join(elevation_datadir, file_name),
                                           usecols=["LATITUDE", "LONGITUDE", "elev_meters"])
            if elevation_df.shape[0] == 0:
                elevation_df = lat_long_elev_df
            else:
                elevation_df = pd.concat([elevation_df, lat_long_elev_df], axis=0)
        return elevation_df

    def preprocess_map_df(self, features_to_keep: List[str], min_year: int = 2014):
        """This function keeps only the features in the features_to_keep list from the original geospatial data
        and from the year greater than or equal to min_year.

        :param features_to_keep: the list of features (columns) to keep.
        :param min_year: the minimum year to keep.
        """
        # filter to only include new well completion since we predict on this
        self.map_df = self.map_df[self.map_df["RECORDTYPE"] == "WellCompletion/New/Production or Monitoring/NA"]
        # filter to only include agriculture, domestic, or public wells
        # Data issues Agriculture is also denoted by "AG"
        self.map_df["USE"] = self.map_df["USE"].fillna("")
        self.map_df["USE"] = self.map_df["USE"].str.lower()
        self.map_df["USE"] = (
            np.where(self.map_df["USE"].str.contains("agri|irrigation"),
                     "Agriculture",
                     np.where(self.map_df["USE"].str.contains("domestic"),
                              "Domestic",
                              np.where(self.map_df["USE"].str.contains("indus|commerc"),
                                       "Industrial",
                                       np.where(self.map_df["USE"].str.contains("public"),
                                                "Public",
                                                "Other")))))
        self.map_df = self.map_df[self.map_df["USE"].isin(["Agriculture", "Domestic", "Public", "Industrial"])]
        self.map_df["TOTALCOMPLETEDDEPTH"] = pd.to_numeric(self.map_df["TOTALCOMPLETEDDEPTH"], errors="coerce")
        # removes depth data that are less than 20"
        self.map_df["TOTALCOMPLETEDDEPTH_CORRECTED"] = self.map_df["TOTALCOMPLETEDDEPTH"].apply(
            lambda x: x if x >= 20 else np.nan)
        # convert date work ended to datetime and filter to only include completed dates that are possible 
        # (not a future date) 
        self.map_df["DATEWORKENDED"] = pd.to_datetime(self.map_df["DATEWORKENDED"], errors="coerce")
        # convert date work ended to datetime and filter to only include completed dates that are possible 
        # (not a future date) 
        self.map_df["DATEWORKENDED"] = pd.to_datetime(self.map_df["DATEWORKENDED"], errors="coerce")
        self.map_df["DATEWORKENDED_CORRECTED"] = self.map_df["DATEWORKENDED"].apply(
            lambda x: x if x < datetime.now() else np.nan)
        # Drop data points with date of NaN
        self.map_df.dropna(subset=["DATEWORKENDED_CORRECTED"], inplace=True)
        # create simple year and month columns
        self.map_df["DATE"] = pd.to_datetime(self.map_df.DATEWORKENDED_CORRECTED)
        self.map_df["YEARWORKENDED"] = self.map_df["DATE"].dt.year
        self.map_df["MONTHWORKENDED"] = self.map_df["DATE"].dt.month
        # Merge missing elevation data
        self.map_df = self.map_df.merge(self.elevation_df, how="left", left_on=["LATITUDE", "LONGITUDE"],
                                        right_on=["LATITUDE", "LONGITUDE"])
        self.map_df.drop(columns=["GROUNDSURFACEELEVATION"], inplace=True)
        self.map_df.rename(columns={"elev_meters": "GROUNDSURFACEELEVATION", "YEARWORKENDED": "YEAR",
                                    "MONTHWORKENDED": "MONTH"}, inplace=True)
        # Keep only the data after min_year and before the current year
        current_year = datetime.now().year
        self.map_df = self.map_df[(self.map_df["YEAR"] >= min_year) & (self.map_df["YEAR"] < current_year)]
        # Keep only the requested features
        self.map_df = self.map_df[features_to_keep]

    def get_well_count_by_year_month(self, count_feature: str = "WCRNUMBER"):
        """This function returns a GeoDataframe of the number of wells per year and month

        :param count_feature: the feature to use for counting the number of wells in each Township-Range.
        :return: a dataframe with the number of wells in each Township-Range
        """
        count_by_township_df = self._get_aggregated_points_by_township(by=["YEAR", "MONTH"],
                                                                      features_to_aggregate=[count_feature],
                                                                      aggfunc="count")
        count_by_township_df.rename(columns={count_feature: "WELL_COUNT"}, inplace=True)
        return count_by_township_df

    def compute_features_by_township(self, features_to_average: List[str], add_well_count: bool = True,
                                     add_well_usage_count: bool = True, count_feature: str = "WCRNUMBER",
                                     count_category_feature: str = "USE",
                                     fill_na_with_zero: bool = True):
        """This function computes the features in the features_to_compute list for each township

        :param features_to_average: the list of features to average.
        :param add_well_count: if True, a feature counting the number of wells per Township-Range is added.
        :param add_well_usage_count: if True, a feature counting the number of wells per usage type and Township-Range
        is added.
        :param count_feature: the feature to use for counting the number of wells in each Township-Range.
        :param count_category_feature: the feature to use for counting the number of wells per usage type.
        :param fill_na_with_zero: if True, the features nin NaN data are filled with 0
        """
        self.keep_only_sjv_data()
        township_features_df = self._get_aggregated_points_by_township(by=["TOWNSHIP_RANGE", "YEAR"],
                                                                      features_to_aggregate=features_to_average,
                                                                      aggfunc="mean", new_feature_suffix="_AVG",
                                                                      fill_na_with_zero=fill_na_with_zero)
        if add_well_count:
            # Get the well count by Township-Range and year
            count_by_township_df = self._get_aggregated_points_by_township(by=["TOWNSHIP_RANGE", "YEAR"],
                                                                           features_to_aggregate=[count_feature],
                                                                           aggfunc="count",
                                                                           fill_na_with_zero=True)
            count_by_township_df.rename(columns={count_feature: "WELL_COUNT"}, inplace=True)
            # Merge the count by township with the township features
            township_features_df = township_features_df.merge(count_by_township_df, how="left",
                                                              left_on=["TOWNSHIP_RANGE", "YEAR", "geometry"],
                                                              right_on=["TOWNSHIP_RANGE", "YEAR", "geometry"]
                                                              )
        if add_well_usage_count:
            usage_count_by_township_df = self._get_category_count_by_township(by=["TOWNSHIP_RANGE", "YEAR"],
                                                                              feature_name=count_category_feature,
                                                                              feature_prefix="WELL_COUNT_")
            township_features_df = township_features_df.merge(usage_count_by_township_df, how="left",
                                                              left_on=["TOWNSHIP_RANGE", "YEAR"],
                                                              right_on=["TOWNSHIP_RANGE", "YEAR"]
                                                              )
        self.map_df = township_features_df