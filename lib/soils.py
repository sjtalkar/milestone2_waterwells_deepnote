import os
import numpy as np
import pandas as pd

from typing import List, Tuple
from lib.wsdatasets import WsGeoDataset


class SoilsDataset(WsGeoDataset):
    """This class loads, processes and exports the Soil dataset"""
    def __init__(self, input_geofiles: List[str] = ["../assets/inputs/soils/map/gsmsoilmu_a_ca.shp"],
                 input_datafile: str = "../assets/inputs/soils/soil_data.csv",
                 merging_keys: List[str] = ["MUKEY", "mukey"]):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles, input_datafile=input_datafile,
                              merging_keys=merging_keys)

    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        return pd.read_csv(input_datafile, delimiter=";")

    def preprocess_map_df(self, features_to_keep: List[str] = ["MUKEY", "geometry"]):
        """This function preprocesses the Soil map dataset by: 1) extracting only the columns: "MUKEY", "geometry". 2)
        changing the type of the "MUKEY" to int64. The function updates the self.map_df dataframe.

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = self.map_df[features_to_keep]
        self.map_df["MUKEY"] = self.map_df["MUKEY"].astype(np.int64)
        self.map_df["YEAR"] = "2016"

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
        for year in ["2014", "2015", "2017", "2018", "2019", "2020", "2021"]:
            map_other_year_df = self.map_df[self.map_df["YEAR"] == "2016"].copy()
            map_other_year_df["YEAR"] = year
            self.map_df = pd.concat([self.map_df, map_other_year_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)
