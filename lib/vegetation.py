import os
import json
import requests
import pandas as pd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import download_and_extract_zip_file


class VegetationDataset(WsGeoDataset):
    """
    This class loads, processes and exports the Existing Vegetation dataset
    """
    def __init__(self, input_geodir: str = "../assets/inputs/vegetation/",
                 saf_cover_type_file: str = "../assets/inputs/vegetation/saf_cover_type_mapping.json"):
        try:
            self._load_local_datasets(input_geodir, saf_cover_type_file)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_geodir, saf_cover_type_file)
            self._load_local_datasets(input_geodir, saf_cover_type_file)

    def _load_local_datasets(self, input_geodir: str, saf_cover_type_file: str):
        """This function loads the Vegetation datasets from the local filesystem.

        :param input_geodir: the path to the vegetation geospatial datasets
        :param saf_cover_type_file: the path to the SAF cover type mapping file
        """
        print("Loading local datasets. Please wait...")
        vegetation_subdir_list = [name for name in os.listdir(input_geodir) if os.path.isdir(
            os.path.join(input_geodir, name))]
        input_geofiles = []
        for vegetation_subdir in vegetation_subdir_list:
            input_geofiles.append(os.path.join(input_geodir, vegetation_subdir, "a00000009.gdbtable"))
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles)
        with open(saf_cover_type_file) as f:
            self.saf_cover_type_mapping = json.load(f)
        print("Loading of datasets complete.")

    def _download_datasets(self, input_geodir: str, cover_type_mapping: str):
        """This function downloads the Vegetation datasets from the web

        :param input_geodir: the directory where to store the vegetation geospatial datasets
        :param cover_type_mapping: the file where the mapping between the SAF cover type code and the forest type will
        be stored
        """
        print(f"Data not found locally.")
        vegetation_datasets_urls = {
            "central_coast": "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.EVMid_R05_CentralCoast.gdb.zip",
            "central_valley": "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.EVMid_R05_CentralValley.gdb.zip"
        }
        for dataset_name, url in vegetation_datasets_urls.items():
            print(f"Downloading the vegetation geospatial dataset '{dataset_name}'. Please wait...")
            download_and_extract_zip_file(url=url, extract_dir=os.path.join(input_geodir, dataset_name))
        print("Downloading the vegetation cover-type-to-name mapping from GitHub repository. Please wait...")
        url = "https://raw.githubusercontent.com/mlnrt/milestone2_waterwells_data/main/vegetation/saf_cover_type_mapping.json"
        file_content = requests.get(url).text
        with open(cover_type_mapping, "w", encoding="utf-8") as f:
            f.write(file_content)
        print("Downloads complete.")

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function preprocesses the Vegetation map dataset by 1) extracting only the columns: "SAF_COVER_TYPE",
        "geometry". 2) renaming the "SAF_COVER_TYPE" column to "VEGETATION_TYPE. 3) Replace the "SAF_COVER_TYPE" codes
         by the forest type names. The function updates the self.map_df
        dataframe.

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = self.map_df[features_to_keep]
        self.map_df.rename(columns={"SAF_COVER_TYPE": "VEGETATION_TYPE"}, inplace=True)
        # Replace forest type code by the forest type name (e.g.replaces "239" by "Pinyon - Juniper")
        self.map_df["VEGETATION_TYPE"] = self.map_df["VEGETATION_TYPE"].apply(
            lambda x: self.saf_cover_type_mapping.get(x, "Non Forest").replace(" - ", "-"))
        self.map_df["YEAR"] = 2019

    def fill_missing_years(self):
        """The Vegetation dataset only contains data updated up to 2019. These data are used to fill-in all the other
        years from 2015 to 2021. The function updates the self.map_df dataframe.
        """
        for year in range(2014, 2022):
            if year != 2019:
                map_other_year_df = self.map_df[self.map_df["YEAR"] == 2019].copy()
                map_other_year_df["YEAR"] = year
                self.map_df = pd.concat([self.map_df, map_other_year_df], axis=0)
        self.map_df.reset_index(inplace=True, drop=True)
