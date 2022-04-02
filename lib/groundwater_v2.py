from datetime import datetime
import pandas as pd
import geopandas as gpd

from typing import List
from lib.wsdatasets import WsGeoDataset

class GroundwaterDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_geofiles: List[str] = [],
                 input_datafile: str = "../assets/inputs/groundwater/groundwater.csv"):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles, input_datafile=input_datafile,
                              merging_keys=["SITE_CODE", "SITE_CODE"])
        # Initializes the Geospatial map_df dataset based on the LATITUDE & LONGITUDE features of the
        # groundwater_stations dataset
        groundwaterstations_df = pd.read_csv(r"../assets/inputs/groundwater/groundwater_stations.csv")
        self.map_df = gpd.GeoDataFrame(
            groundwaterstations_df,
            geometry=gpd.points_from_xy(
                groundwaterstations_df.LONGITUDE,
                groundwaterstations_df.LATITUDE
            ))
        #Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs("epsg:4326")

    def preprocess_data_df(self, features_to_keep: List[str] = ["SITE_CODE", "GSE_GWE", "YEAR"], min_year: int = 2014):
        """This function keeps the GSE_GWE feature for the spring months.

        :param features_to_keep: the list of features (columns) to keep.
        :param min_year: the minimum year to keep.
        """
        # create simple year and month columns
        self.data_df["MSMT_DATE"] = pd.to_datetime(self.data_df.MSMT_DATE)
        self.data_df["YEAR"] = self.data_df["MSMT_DATE"].dt.year
        self.data_df["MONTH"] = self.data_df["MSMT_DATE"].dt.month
        # Retain only those records that have Groundwater measurements
        self.data_df = self.data_df[~self.data_df["GSE_GWE"].isnull()] # 2325741
        # drop the rows that have incorrect measurements that of 0 or less
        self.data_df = self.data_df[self.data_df["GSE_GWE"] > 0]
        # filter for just the spring measurements
        spring_months = [1, 2, 3, 4]
        self.data_df = self.data_df[self.data_df["MONTH"].isin(spring_months)]
        # Keep only the necessary features
        self.data_df = self.data_df[features_to_keep]
        # Keep only the data after min_year and before the current year
        current_year = datetime.now().year
        self.data_df = self.data_df[(self.data_df["YEAR"] >= min_year) & (self.data_df["YEAR"] < current_year)]

    def preprocess_map_df(self, features_to_keep: List[str] = ["SITE_CODE", "COUNTY", "geometry"]):
        """This function keeps only the SITE_CODE, COUNTY and geometry features in the original geospatial data."""
        self.map_df.rename(columns={"COUNTY_NAME": "COUNTY"}, inplace=True)
        self.map_df = self.map_df[features_to_keep]


