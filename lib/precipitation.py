from lib.wsdatasets import WsGeoDataset
from fiona.errors import DriverError
from lib.download import download_precipitation_datasets


class PrecipitationDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, input_stationfile: str = "../assets/inputs/precipitation/map/precipitation_stations.shp",
                 input_datafile: str = "../assets/inputs/precipitation/precipitation_data.csv"):
        """ The initialization of the PrecipitationDataset class automatically scrapes the monthly precipitation data
        for the state of California in the data_df dataframe and downloads the weather's station location into the
        map_df dataframe.

        :param input_stationfile: the path to the CSV file containing the station dataIf it does not exists, the data
        will be scraped from the web and stored into this file.
        :param input_datafile: the path to the CSV file containing the additional data dataset. If it does not exist,
        the data will be scraped from the web and stored into this file.
        :param year_start: The year to start collecting the data from.
        :param year_end: The year to end collecting the data from.
        """
        self.input_geofile = input_stationfile
        self.input_datafile = input_datafile
        # Try to load the dataset for pre-downloaded files. If not scrap the data from the web and save them
        try:
            print("Loading local datasets. Please wait...")
            WsGeoDataset.__init__(self, input_geofiles=[input_stationfile], input_datafile=input_datafile,
                                  merging_keys=["STATION_ID", "STATION_ID"])
            print("Loading of datasets complete.")
        except (FileNotFoundError, DriverError):
            # Load the pre-packaged datasets and then initialize the class
            self._download_datasets(input_stationfile, input_datafile)
            WsGeoDataset.__init__(self, input_geofiles=[input_stationfile], input_datafile=input_datafile,
                                  merging_keys=["STATION_ID", "STATION_ID"])
            print("Loading of datasets complete.")

    def _download_datasets(self, input_stationfile: str, input_datafile: str):
        """This function downloads the pre-packaged precipitation dataset from the web

        :param input_stationfile: the path to the Shapefile file containing the precipitation station geospatial data
        :param input_datafile: the path to the CSV file containing the additional data dataset
        """
        print("Data not found locally.")
        download_precipitation_datasets(input_stationfile, input_datafile)
        print("Downloads complete.")


