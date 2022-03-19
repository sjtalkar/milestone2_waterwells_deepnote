import os
import numpy as np
import pandas as pd

from typing import List, Tuple
from lib.wsdatasets import WsGeoDataset


class VegetationDataset(WsGeoDataset):
    """This class loads, processes and exports the Soil dataset"""
    def __init__(self, input_geofiles: List[str] = ["../assets/inputs/vegetation/central_coast/a00000009.gdbtable",
                                                    "../assets/inputs/vegetation/central_valley/a00000009.gdbtable"]):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles)

    def preprocess_map_df(self, features_to_keep: List[str] = ["SAF_COVER_TYPE", "geometry"]):
        """This function preprocesses the Soil map dataset by 1) extracting only the columns: "SAF_COVER_TYPE",
        "geometry". 2) renaming the "SAF_COVER_TYPE" column to "VEGETATION_TYPE. The function updates the self.map_df
        dataframe.

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = self.map_df[features_to_keep]
        self.map_df.rename(columns={"SAF_COVER_TYPE": "VEGETATION_TYPE"}, inplace=True)
        self.map_df["YEAR"] = "2019"

    def fill_missing_years(self):
        """The Vegetation dataset only contains data updated up to 2019. These data are used to fill-in all the other
        years from 2015 to 2021. The function updates the self.map_df dataframe.
        """
        for year in range(2015, 2022):
            if year != 2019:
                map_other_year_df = self.map_df[self.map_df["YEAR"] == "2019"].copy()
                map_other_year_df["YEAR"] = str(year)
                self.map_df = pd.concat([self.map_df, map_other_year_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)
