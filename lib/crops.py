import json
import pandas as pd
import geopandas as gpd

from typing import List, Tuple, Dict
from lib.wsdatasets import WsGeoDataset


class CropsDataset(WsGeoDataset):
    """This class loads, processes and exports the Crops dataset"""
    def __init__(self, input_geofiles: Dict[str, str] = {
            "2014": "../assets/inputs/crops/crops_2014/i15_Crop_Mapping_2014.shp",
            "2016": "../assets/inputs/crops/crops_2016/i15_Crop_Mapping_2016.shp",
            "2018": "../assets/inputs/crops/crops_2018/i15_Crop_Mapping_2018.shp"},
            crop_name_to_type_file: str = "../assets/inputs/crops/crop_name_to_type_mapping.json"):
        """Initialization of the 2014, 2016 and 2018 Crops datasets. The function loads the elf.map_2014_df,
        elf.map_2016_df and elf.map_2018_df dataframes

        :param input_geofiles: dictionnary of of geospatial files to vertically concatenate in the format
        {"year": "file path"}. The dictionnary must at least contains the data for the years 2014, 2016 and 2018
        """
        if not set(input_geofiles.keys()).issubset({"2014", "2016", "2018"}):
            raise KeyError(
                "The input_geofiles dictionnary must at least contain the data files for the years 2014, 2016 and 2018")
        WsGeoDataset.__init__(self, [])
        self.map_2014_df = self._read_geospatial_file(input_geofiles.get("2014"))
        self.map_2016_df = self._read_geospatial_file(input_geofiles.get("2016"))
        self.map_2018_df = self._read_geospatial_file(input_geofiles.get("2018"))
        with open(crop_name_to_type_file) as f:
            self.crop_name_to_type_mapping = json.load(f)

    def preprocess_map_df(self, features_to_keep: List[str] = ["YEAR", "CROP_TYPE", "geometry"],
                          get_crops_details: bool=False):
        """This function preprocesses the Crops map datasets (2014, 2016, 2018) by: 1) extracting only the summer crop
        class in each dataset. 2) adding a YEAR feature. 3) merging the contiguous land areas of the same crop class
        together. Each dataset is updated individually. The final self.map_df dataset only concatenates the 2016 and
        2018 datasets as the analysis only use data from 2015. The function updates the map dataframes.

        :param features_to_keep: the list of features (columns) to keep.
        :param get_drops_details: whether to extract the crops data at the crop level instead of the crop class level.
        """
        crop_type_mapping = {
            "2014": "DWR_Standa",
            "2016": "CLASS2",
            "2018": "CLASS2",
        }
        if get_crops_details:
            crop_type_mapping = {
                "2014": "DWR_Standa",
                "2016": "CROPTYP2",
                "2018": "CROPTYP2",
            }
        # Transform the 2014 dataset
        self.map_2014_df["YEAR"] = "2014"
        # If we just want the crop class (get_crops_details=False) we extract the first letter of the DWR_Standa
        # column. Otherwise we need to extract the crop name ( after the "|" character in the DWR_Standa column
        # and get the corresponding crop type as definined in the CROPTYP1 (combination of crop CLASS and SUBCLASS) in
        # the 2016 and 2018 datasets
        self.map_2014_df["CROP_TYPE"] = self.map_2014_df[crop_type_mapping["2014"]].apply(
            lambda x: x[0] if not get_crops_details else self.crop_name_to_type_mapping.get(x[0].split("|")[1], "X"))
        self.map_2014_df = self.map_2014_df[features_to_keep]
        # Merge contiguous land areas of the same crop class together
        self.map_2014_df = self.map_2014_df.dissolve(by=["YEAR", "CROP_TYPE"]).reset_index()\
            #.explode(ignore_index=True)

        # Transform the 2016 dataset
        self.map_2016_df["YEAR"] = "2016"
        # self.map_2016_df["IRRIGATED"] = self.map_2016_df["IRR_TYP1PA"].apply(lambda x: irrigated_mapping.get(x, 0))
        self.map_2016_df.rename(columns={crop_type_mapping["2016"]: "CROP_TYPE"}, inplace=True)
        self.map_2016_df = self.map_2016_df[features_to_keep]
        # Merge contiguous land areas of the same crop class together
        self.map_2016_df = self.map_2016_df.dissolve(by=["YEAR", "CROP_TYPE"]).reset_index()

        # Transform the 2018 dataset
        self.map_2018_df["YEAR"] = "2018"
        # self.map_2018_df["IRRIGATED"] = self.map_2018_df["IRR_TYP1PA"].apply(lambda x: irrigated_mapping.get(x, 0))
        self.map_2018_df.rename(columns={crop_type_mapping["2018"]: "CROP_TYPE"}, inplace=True)
        self.map_2018_df = self.map_2018_df[features_to_keep]
        # Merge contiguous land areas of the same crop class together
        self.map_2018_df = self.map_2018_df.dissolve(by=["YEAR", "CROP_TYPE"]).reset_index()

        # Concatenate the 2016 and 2018 datasets vertically.
        # The 2014 dataset is not included in the map dataset as for this analysis
        # We use data from 2015
        self.map_df = pd.concat([self.map_2016_df, self.map_2018_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)

    def fill_townships_with_no_data(self):
        """Some townships have no Crops data. This function assigns the "X - Unclassified" Crop class to
        these townships for all the years where they have no data"""
        all_townships = set(self.sjv_township_range_df["TOWNSHIP"].unique())
        for year in self.map_df["YEAR"].unique():
            year_df = self.map_df[self.map_df["YEAR"] == year]
            missing_townships = all_townships - set(year_df["TOWNSHIP"].unique())
            missing_townships_df = self.sjv_township_range_df[self.sjv_township_range_df["TOWNSHIP"].
                isin(missing_townships)]
            missing_townships_df["YEAR"] = year
            missing_townships_df["CROP_TYPE"] = "X"
            self.map_df = pd.concat([self.map_df, missing_townships_df], axis=0)


    def fill_missing_years(self):
        """The Crops datasets contain data for the years 2014, 2016 and 2018. This function uses the 2014 data to fill
        the 2015 data, the 2016 for 2017 and the 2018 for the years 2019~

        :return: the function updates the self.map_df dataframe
        """
        # Use the 2014 data for 2015
        map_2015_df = self.map_df[self.map_df["YEAR"] == "2014"].copy()
        map_2015_df["YEAR"] = "2015"
        # Use the 2016 data for 2017
        map_2017_df = self.map_df[self.map_df["YEAR"] == "2016"].copy()
        map_2017_df["YEAR"] = "2017"
        self.map_df = pd.concat([self.map_df, map_2015_df, map_2017_df], axis=0)
        # For years post 2018, use the 2018 data
        for year in ["2019", "2020", "2021"]:
            map_post_2018_df = self.map_df[self.map_df["YEAR"] == "2018"].copy()
            map_post_2018_df["YEAR"] = year
            self.map_df = pd.concat([self.map_df, map_post_2018_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)