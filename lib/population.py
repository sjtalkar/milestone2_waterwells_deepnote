import pandas as pd
import geopandas as gpd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import downoad_population_datasets


class PopulationDataset(WsGeoDataset):
    """This class loads, processes and exports the Population dataset"""
    def __init__(self, input_datafile: str = "../assets/inputs/population/population.csv",
                 tract_geofile: str = "../assets/inputs/population/tracts_map/tl_2019_06_tract.shp"):
        """Initialization of the Population dataset

        :param input_datafile: the file containing the population data
        :param tract_geofile: the file containing the shapefile of the population census Tracts
        """

        try:
            self._load_local_datasets(input_datafile, tract_geofile)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_datafile, tract_geofile)
            self._load_local_datasets(input_datafile, tract_geofile)

    def _load_local_datasets(self, input_datafile: str, tract_geofile: str):
        """This function loads the Population datasets from the local filesystem.

        :param input_datafile: the file containing the population data
        :param tract_geofile: the file containing the shapefile of the population census Tracts
        """
        print("Loading local datasets. Please wait...")
        super().__init__(input_geofiles=[tract_geofile], input_datafile=input_datafile,
                         merging_keys=["TRACT_ID", "TRACT_ID"])
        print("Loading of datasets complete.")

    def _download_datasets(self, input_datafile: str, tract_geofile: str):
        """This function downloads the population datasets from the web

        :param input_datafile: the file where to store the population data
        :param tract_geofile: the file where to store the shapefile of the population census Tracts
        """
        print("Data not found locally.")
        downoad_population_datasets(input_datafile, tract_geofile)
        print("Downloads complete.")

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function preprocesses the geospatial Tract data

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = gpd.clip(self.map_df, self.ca_boundaries.geometry[0])
        self.map_df["TRACT_ID"] = self.map_df["STATEFP"] + self.map_df["COUNTYFP"] + self.map_df["TRACTCE"]
        self.map_df = self.map_df[features_to_keep]

    def preprocess_data_df(self):
        """This function preprocesses the Soil data dataset by:
        * filling the map unit with soil taxonomy orders as NaN with the description in the "compname" column
        * merge the soil taxonomy order and hydrologic group as one SOIL_TYPE feature
        * use "max polling" on each map unit to assign it only the dominant SOIL_TYPE
        * extract only the columns: "mukey", "DOMINANT_SOIL_TYPE"
        """
        def get_trend(df: pd.DataFrame, year: int) -> pd.DataFrame:
            trend_df = df[df["YEAR"].isin([year-1, year])].copy()
            trend_df = pd.pivot_table(trend_df, index="TRACT_ID", columns="YEAR",
                                      values="TOTAL_POPULATION").reset_index()
            trend_df["TREND"] = 1 + ((trend_df[year] - trend_df[year-1]) / trend_df[year-1])
            return trend_df

        self.data_df["TRACT_ID"] = self.data_df["TRACT_ID"].astype(str)
        self.data_df["TRACT_ID"] = "0" + self.data_df["TRACT_ID"]
        # Now that we have all data we compute the population density per year and tract
        self.data_df["POPULATION_DENSITY"] = self.data_df["TOTAL_POPULATION"] / self.data_df["LAND_AREA"]
        self.data_df = self.data_df[["TRACT_ID", "POPULATION_DENSITY", "YEAR"]]

    def discard_partial_2020_data(self):
        """This function discards the partial 2020 data"""
        self.map_df = self.map_df[self.map_df["YEAR"] != 2020]
