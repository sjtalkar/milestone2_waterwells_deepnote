import json
import requests
import os
import zipfile
import pandas as pd

from typing import List
from io import BytesIO
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset


class CropsDataset(WsGeoDataset):
    """This class loads, processes and exports the Crops dataset"""
    def __init__(self, input_geodir: str = "../assets/inputs/crops/",
                 crop_name_to_type_file: str = "../assets/inputs/crops/crop_name_to_type_mapping.json"):
        """Initialization of the 2014, 2016 and 2018 Crops datasets. The function loads the elf.map_2014_df,
        elf.map_2016_df and elf.map_2018_df dataframes

        :param input_geodir: the directory containing the crops geospatial subfolders (subfolder example: crops_2014)
        :param crop_name_to_type_file: the file containing the crop name to type mapping
        """
        WsGeoDataset.__init__(self, [])
        try:
            self.map_2014_df = self._read_geospatial_file(f"{input_geodir}crops_2014/i15_Crop_Mapping_2014.shp")
            self.map_2016_df = self._read_geospatial_file(f"{input_geodir}crops_2016/i15_Crop_Mapping_2016.shp")
            self.map_2018_df = self._read_geospatial_file(f"{input_geodir}crops_2018/i15_Crop_Mapping_2018.shp")
        except (FileNotFoundError, DriverError):
            self._download_crops_datasets(input_geodir)
            self.map_2014_df = self._read_geospatial_file(f"{input_geodir}crops_2014/i15_Crop_Mapping_2014.shp")
            self.map_2016_df = self._read_geospatial_file(f"{input_geodir}crops_2016/i15_Crop_Mapping_2016.shp")
            self.map_2018_df = self._read_geospatial_file(f"{input_geodir}crops_2018/i15_Crop_Mapping_2018.shp")
        try:
            with open(crop_name_to_type_file) as f:
                self.crop_name_to_type_mapping = json.load(f)
        except FileNotFoundError:
            self._download_crop_name_mapping(crop_name_to_type_file)
            with open(crop_name_to_type_file) as f:
                self.crop_name_to_type_mapping = json.load(f)

    def _download_crops_datasets(self, input_geodir: str):
        """This function downloads the crops datasets from the web

        :param input_geodir: the directory where to store the crops geospatial datasets
        """
        url_base = "https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource"
        crops_datasets_urls = {
            "crops_2014": "/3bba74e2-a992-48db-a9ed-19e6fabb8052/download/i15_crop_mapping_2014_shp.zip",
            "crops_2016": "/3b57898b-f013-487a-b472-17f54311edb5/download/i15_crop_mapping_2016_shp.zip",
            "crops_2018": "/2dde4303-5c83-4980-a1af-4f321abefe95/download/i15_crop_mapping_2018_shp.zip"
        }
        for dataset_name, url in crops_datasets_urls.items():
            os.makedirs(os.path.join(input_geodir, dataset_name), exist_ok=True)
            # Download the dataset content
            geofile_content = requests.get(url_base + url).content
            # extract the zip files directly from the content
            with zipfile.ZipFile(BytesIO(geofile_content)) as zf:
                # For each members of the archive
                for member in zf.infolist():
                    # If it's a directory, continue
                    if member.filename[-1] == '/': continue
                    # Else write its content to the dataset root folder
                    with open(os.path.join(input_geodir, dataset_name, os.path.basename(member.filename)), "wb") as outfile:
                        outfile.write(zf.read(member))

    def _download_crop_name_mapping(self, crop_name_to_type_file: str):
        """This function downloads the crop name to type mapping file from the web

        :param crop_name_to_type_file: the file name where to store the crop name to type mapping
        """
        url = "https://raw.githubusercontent.com/mlnrt/milestone2_waterwells_data/main/crops/crop_name_to_type_mapping.json"
        file_content = requests.get(url).text
        with open(crop_name_to_type_file, "w") as f:
            f.write(file_content)

    def preprocess_map_df(self, features_to_keep: List[str], get_crops_details: bool = False):
        """This function preprocesses the Crops map datasets (2014, 2016, 2018) by: 1) extracting only the summer crop
        class in each dataset. 2) adding a YEAR feature. 3) merging the contiguous land areas of the same crop class
        together. Each dataset is updated individually. The final self.map_df dataset only concatenates the 2016 and
        2018 datasets as the analysis only use data from 2015. The function updates the map dataframes.

        :param features_to_keep: the list of features (columns) to keep.
        :param get_crops_details: whether to extract the crops data at the crop level instead of the crop class level.
        """
        crop_type_mapping = {
            "2014": "DWR_Standa",
            "2016": "CLASS2",
            "2018": "CLASS2",
        }
        if get_crops_details:
            crop_type_mapping = {
                "2014": "Crop2014",
                "2016": "CROPTYP2",
                "2018": "CROPTYP2",
            }
        # Transform the 2014 dataset
        self.map_2014_df["YEAR"] = 2014
        # If we just want the crop class (get_crops_details=False) we extract the first letter of the DWR_Standa
        # column. Otherwise we need to extract the crop name ( after the "|" character in the DWR_Standa column
        # and get the corresponding crop type as definined in the CROPTYP1 (combination of crop CLASS and SUBCLASS) in
        # the 2016 and 2018 datasets
        self.map_2014_df["CROP_TYPE"] = self.map_2014_df[crop_type_mapping["2014"]].apply(
            lambda x: x[0] if not get_crops_details
            else self.crop_name_to_type_mapping.get(x.lower(), "X"))
        self.map_2014_df = self.map_2014_df[features_to_keep]

        # Transform the 2016 dataset
        self.map_2016_df["YEAR"] = 2016
        # self.map_2016_df["IRRIGATED"] = self.map_2016_df["IRR_TYP1PA"].apply(lambda x: irrigated_mapping.get(x, 0))
        self.map_2016_df.rename(columns={crop_type_mapping["2016"]: "CROP_TYPE"}, inplace=True)
        self.map_2016_df = self.map_2016_df[features_to_keep]

        # Transform the 2018 dataset
        self.map_2018_df["YEAR"] = 2018
        # self.map_2018_df["IRRIGATED"] = self.map_2018_df["IRR_TYP1PA"].apply(lambda x: irrigated_mapping.get(x, 0))
        self.map_2018_df.rename(columns={crop_type_mapping["2018"]: "CROP_TYPE"}, inplace=True)
        self.map_2018_df = self.map_2018_df[features_to_keep]

        # Concatenate the 2016 and 2018 datasets vertically.
        # The 2014 dataset is not included in the map dataset as for this analysis
        # We use data from 2015
        self.map_df = pd.concat([self.map_2014_df, self.map_2016_df, self.map_2018_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)

    def fill_missing_years(self):
        """The Crops datasets contain data for the years 2014, 2016 and 2018. This function uses the 2014 data to fill
        the 2015 data, the 2016 for 2017 and the 2018 for the years 2019~

        :return: the function updates the self.map_df dataframe
        """
        # Use the 2014 data for 2015
        map_2015_df = self.map_df[self.map_df["YEAR"] == 2014].copy()
        map_2015_df["YEAR"] = 2015
        # Use the 2016 data for 2017
        map_2017_df = self.map_df[self.map_df["YEAR"] == 2016].copy()
        map_2017_df["YEAR"] = 2017
        self.map_df = pd.concat([self.map_df, map_2015_df, map_2017_df], axis=0)
        # For years post 2018, use the 2018 data
        for year in [2019, 2020, 2021]:
            map_post_2018_df = self.map_df[self.map_df["YEAR"] == 2018].copy()
            map_post_2018_df["YEAR"] = year
            self.map_df = pd.concat([self.map_df, map_post_2018_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)
