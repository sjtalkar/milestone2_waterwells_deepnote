import requests
import os
import numpy as np
import pandas as pd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset


class SoilsDataset(WsGeoDataset):
    """This class loads, processes and exports the Soil dataset"""
    def __init__(self, input_geofile: str = "../assets/inputs/soils/map/gsmsoilmu_a_ca.shp",
                 input_datafile: str = "../assets/inputs/soils/soil_data.csv"):
        try:
            WsGeoDataset.__init__(self, input_geofiles=[input_geofile], input_datafile=input_datafile,
                                  merging_keys=["MUKEY", "mukey"])
        except (FileNotFoundError, DriverError):
            self._download_datasets(os.path.dirname(input_geofile), input_datafile)
            WsGeoDataset.__init__(self, input_geofiles=[input_geofile], input_datafile=input_datafile,
                                  merging_keys=["MUKEY", "mukey"])

    def _download_datasets(self, input_geodir: str, input_datafile: str):
        """This function downloads the Soil geospatial and data datasets from a GitHub repository where we extracted the
        data of interest.

        :param input_geodir: the path where to store the Soil geospatial dataset
        :param input_datafile: the file name where to store the Soil data dataset
        """
        os.makedirs(input_geodir, exist_ok=True)
        data_url = "https://raw.githubusercontent.com/mlnrt/milestone2_waterwells_data/main/soils/soil_data.csv"
        datafile_content = requests.get(data_url).text
        with open(input_datafile, "w", encoding="utf-8") as f:
            f.write(datafile_content)
        geofile_baseurl = "https://raw.githubusercontent.com/mlnrt/milestone2_waterwells_data/main/soils/map/"
        files_basename = "gsmsoilmu_a_ca."
        extensions = ["dbf", "prj", "shp", "shx"]
        for ext in extensions:
            geofile_content = requests.get(geofile_baseurl + files_basename + ext).content
            with open(os.path.join(input_geodir, files_basename + ext), "wb") as f:
                f.write(geofile_content)

    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        return pd.read_csv(input_datafile, delimiter=";")

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function preprocesses the Soil map dataset by: 1) extracting only the columns: "MUKEY", "geometry". 2)
        changing the type of the "MUKEY" to int64. The function updates the self.map_df dataframe.

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = self.map_df[features_to_keep]
        self.map_df["MUKEY"] = self.map_df["MUKEY"].astype(np.int64)
        self.map_df["YEAR"] = 2016

    def preprocess_data_df(self):
        """This function preprocesses the Soil data dataset by:
        * filling the map unit with soil taxonomy orders as NaN with the description in the "compname" column
        * merge the soil taxonomy order and hydrologic group as one SOIL_TYPE feature
        * use "max polling" on each map unit to assign it only the dominant SOIL_TYPE
        * extract only the columns: "mukey", "DOMINANT_SOIL_TYPE"
        """
        self.data_df["taxorder"].fillna(self.data_df["compname"], inplace=True)
        self.data_df["SOIL_TYPE"] = self.data_df["taxorder"] + "_" + self.data_df["hydgrp"].fillna("")
        self.data_df = self.data_df[["mukey", "comppct_r", "SOIL_TYPE"]]
        self.data_df = self.data_df.groupby(by=["mukey", "SOIL_TYPE"]).sum()
        self.data_df.reset_index(inplace=True)
        # Keep only the main soil for each map unit
        self.data_df = self.data_df.loc[self.data_df.groupby("mukey")["comppct_r"].idxmax()].reset_index(drop=True)
        self.data_df.drop(["comppct_r"], axis=1, inplace=True)
        self.data_df.rename(columns={"SOIL_TYPE": "DOMINANT_SOIL_TYPE"}, inplace=True)

    def fill_missing_years(self):
        """The Soils dataset only contains data from the 2016 soil survey. As we don't expect the soil nature to
        change from year to year, the 2016 data are copied to all the other years from 2015. The function updates the
        self.map_df dataframe.
        """
        for year in [2014, 2015, 2017, 2018, 2019, 2020, 2021]:
            map_other_year_df = self.map_df[self.map_df["YEAR"] == 2016].copy()
            map_other_year_df["YEAR"] = year
            self.map_df = pd.concat([self.map_df, map_other_year_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)
