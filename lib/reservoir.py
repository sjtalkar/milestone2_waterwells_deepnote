from typing import List
from lib.wsdatasets import WsGeoDataset
from fiona.errors import DriverError
from lib.download import download_reservoir_datasets


class ReservoirDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, input_stationfile: str = "../assets/inputs/reservoir/map/reservoir_stations.shp",
                 input_datafile: str = "../assets/inputs/reservoir/reservoir_data.csv"):
        """ The initialization of the ReservoirDataset class automatically scrapes the weekly reservoir data
        for the state of California in the data_df dataframe and downloads the reservoir station location into the
        map_df dataframe.

        :param input_stationfile: the path to the CSV file containing the station dataIf it does not exists, the data
        will be scrapped from the web and stored into this file.
        :param input_datafile: the path to the CSV file containing the additional data dataset. If it does not exists,
        the data will be scrapped from the web and stored into this file.
        """
        # Try to load the dataset for pre-downloaded files. If not scrap the data from the web and save them
        try:
            print("Loading local datasets. Please wait...")
            super().__init__(input_geofiles=[input_stationfile], input_datafile=input_datafile,
                             merging_keys=["STATION_ID", "STATION_ID"])
            print("Loading of datasets complete.")
        except (FileNotFoundError, DriverError):
            # Load the pre-packaged datasets and then initialize the class
            self._download_datasets(input_stationfile, input_datafile)
            super().__init__(input_geofiles=[input_stationfile], input_datafile=input_datafile,
                             merging_keys=["STATION_ID", "STATION_ID"])
            print("Loading of datasets complete.")

    def _download_datasets(self, input_stationfile: str, input_datafile: str):
        """This function downloads the pre-packaged reservoir dataset from the web

        :param input_stationfile: the path to the Shapefile file containing the reservoir station geospatial data
        :param input_datafile: the path to the CSV file containing the additional data dataset
        """
        print("Data not found locally.")
        download_reservoir_datasets(input_stationfile, input_datafile)
        print("Downloads complete.")

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function keeps only the features in the features_to_keep list from the original geospatial data.

        :param features_to_keep: the list of features (columns) to keep."""
        self.map_df = self.map_df[features_to_keep].drop_duplicates()
