import os
import json

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset
from lib.download import download_vegetation_datasets


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
        download_vegetation_datasets(input_geodir, cover_type_mapping)
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
