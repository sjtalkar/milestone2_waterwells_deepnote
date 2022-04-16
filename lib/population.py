import requests
import os
import pickle
import pandas as pd
import geopandas as gpd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset


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
        WsGeoDataset.__init__(self, input_geofiles=[tract_geofile], input_datafile=input_datafile,
                              merging_keys=["TRACT_ID", "TRACT_ID"])
        print("Loading of datasets complete.")

    def _download_datasets(self, input_datafile: str, tract_geofile: str):
        """This function downloads the crops datasets from the web

        :param input_datafile: the file where to store the population data
        :param tract_geofile: the file where to store the shapefile of the population census Tracts
        """
        print("Data not found locally.")
        os.makedirs(os.path.dirname(input_datafile), exist_ok=True)
        print("Downloading the pre-packaged 2014-2020 California Census population estimates at the Tract level."
              " Please wait...")
        url = "https://raw.githubusercontent.com/mlnrt/milestone2_waterwells_data/main/population/population.csv"
        file_content = requests.get(url).text
        with open(input_datafile, "w", encoding="utf-8") as f:
            f.write(file_content)
        print("Downloading the geospatial data of the population census Tracts. Please wait...")
        tract_url = "https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_06_tract.zip"
        self._download_and_extract_zip_file(url=tract_url,
                                            extract_dir=os.path.dirname(tract_geofile))
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
        # The year 2020 has missing data, we estimate them for the 2018-2019 data.
        trend_df = get_trend(self.data_df, year=2019)
        year_2020_df = self.data_df[self.data_df["YEAR"] == 2020].copy()
        tract_ids_2020 = list(year_2020_df["TRACT_ID"].unique())
        missing_2020_df = self.data_df[(self.data_df["YEAR"] == 2019) & (~self.data_df["TRACT_ID"].isin(tract_ids_2020))].copy()
        missing_2020_df["YEAR"] = 2020
        missing_2020_df = missing_2020_df.merge(trend_df[["TRACT_ID", "TREND"]], on="TRACT_ID", how="left")
        missing_2020_df["TOTAL_POPULATION"] = round(missing_2020_df["TREND"] * missing_2020_df["TOTAL_POPULATION"])
        missing_2020_df.drop(columns=["TREND"], inplace=True)
        self.data_df = pd.concat([self.data_df, missing_2020_df], axis=0)
        # We are missing the 2021 data. We approximate them as follow:
        # For every Tract, we take the trend of the population density of the previous year and use that
        # to estimate the population density of 2021 from 2020.
        trend_df = get_trend(self.data_df, year=2020)
        year_2021_df = self.data_df[self.data_df["YEAR"] == 2020].copy()
        year_2021_df["YEAR"] = 2021
        year_2021_df = year_2021_df.merge(trend_df[["TRACT_ID", "TREND"]], on="TRACT_ID")
        year_2021_df["TOTAL_POPULATION"] = round(year_2021_df["TREND"] * year_2021_df["TOTAL_POPULATION"])
        year_2021_df.drop(columns=["TREND"], inplace=True)
        self.data_df = pd.concat([self.data_df, year_2021_df], axis=0)
        self.data_df.reset_index(inplace=True, drop=True)
        # Now that we have all data we compute the population density per year and tract
        self.data_df["POPULATION_DENSITY"] = self.data_df["TOTAL_POPULATION"] / self.data_df["LAND_AREA"]
        self.data_df = self.data_df[["TRACT_ID", "POPULATION_DENSITY", "YEAR"]]
