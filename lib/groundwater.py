import pandas as pd
import geopandas as gpd

from datetime import datetime
from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import download_groundwater_datasets

class GroundwaterDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_measurements_file: str = "../assets/inputs/groundwater/groundwater_measurements.csv",
                 input_stations_file: str = r"../assets/inputs/groundwater/groundwater_stations.csv"):
        try:
            self._load_local_datasets(input_measurements_file, input_stations_file)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_measurements_file, input_stations_file)
            self._load_local_datasets(input_measurements_file, input_stations_file)

    def _load_local_datasets(self, input_measurements_file: str, input_stations_file: str):
        """This function loads the groundwater measurements dataset and the groundwater stations dataset from the
        local file system.

        :param input_measurements_file: the path to the measurements dataset.
        :param input_stations_file: the path to the stations dataset.
        """
        print("Loading local datasets. Please wait...")
        WsGeoDataset.__init__(self, input_geofiles=[], input_datafile=input_measurements_file,
                              merging_keys=["SITE_CODE", "SITE_CODE"])
        # Initializes the Geospatial map_df dataset based on the LATITUDE & LONGITUDE features of the
        # groundwater_stations dataset
        groundwaterstations_df = pd.read_csv(input_stations_file)
        self.map_df = gpd.GeoDataFrame(
            groundwaterstations_df,
            geometry=gpd.points_from_xy(
                groundwaterstations_df.longitude,
                groundwaterstations_df.latitude
            ))
        # Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs("epsg:4326")
        print("Loading of datasets complete.")

    def _download_datasets(self, input_measurements_file: str, input_stations_file: str):
        """This function downloads the groundwater measurements dataset and the groundwater stations dataset from the
        web.

        :param input_measurements_file: the path where to store the measurements dataset.
        :param input_stations_file: the path where to store the stations dataset.
        """
        print("Data not found locally.")
        download_groundwater_datasets(input_measurements_file, input_stations_file)
        print("Downloads complete.")

    def preprocess_data_df(self, features_to_keep: List[str], min_year: int = 2014):
        """This function keeps the GSE_GWE feature for the spring months.
        :param features_to_keep: the list of features (columns) to keep.
        :param min_year: the minimum year to keep.
        """
        # create simple year and month columns
        self.data_df["MSMT_DATE"] = pd.to_datetime(self.data_df.MSMT_DATE)
        self.data_df["YEAR"] = self.data_df["MSMT_DATE"].dt.year
        df = self.data_df.copy()
        df = df[df.YEAR >= min_year]
        df.drop(columns=["YEAR"], inplace=True)
        df.to_csv("../assets/inputs/groundwater/groundwater_short.csv")
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

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function keeps only the features in the features_to_keep list from the original geospatial data.
        :param features_to_keep: the list of features (columns) to keep."""
        self.map_df.rename(columns={"COUNTY_NAME": "COUNTY"}, inplace=True)
        self.map_df = self.map_df[features_to_keep]


