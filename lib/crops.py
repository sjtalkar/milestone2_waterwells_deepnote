import json
import pandas as pd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import download_crops_datasets


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
            self._load_local_datasets(input_geodir, crop_name_to_type_file)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_geodir, crop_name_to_type_file)
            self._load_local_datasets(input_geodir, crop_name_to_type_file)

    def _load_local_datasets(self, input_geodir: str, crop_name_to_type_file: str):
        """This function loads the crops datasets from the local filesystem.

        :param input_geodir: the directory containing the crops geospatial subfolders (subfolder example: crops_2014)
        :param crop_name_to_type_file: the file containing the crop name to type mapping
        """
        print("Loading local datasets. Please wait...")
        self.map_2014_df = self._read_geospatial_file(f"{input_geodir}crops_2014/i15_Crop_Mapping_2014.shp")
        self.map_2016_df = self._read_geospatial_file(f"{input_geodir}crops_2016/i15_Crop_Mapping_2016.shp")
        self.map_2018_df = self._read_geospatial_file(f"{input_geodir}crops_2018/i15_Crop_Mapping_2018.shp")
        with open(crop_name_to_type_file) as f:
            self.crop_name_to_type_mapping = json.load(f)
        print("Loading of datasets complete.")

    def _download_datasets(self, input_geodir: str, crop_name_to_type_file: str):
        """This function downloads the crops datasets from the web

        :param input_geodir: the directory where to store the crops geospatial datasets
        :param crop_name_to_type_file: the file name where to store the crop name to type mapping
        """
        print(f"Data not found locally.")
        download_crops_datasets(input_geodir, crop_name_to_type_file)
        print("Downloads complete.")

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

