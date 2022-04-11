import requests
import concurrent.futures
import pandas as pd
import geopandas as gpd

from datetime import datetime
from bs4 import BeautifulSoup
from typing import List
from lib.wsdatasets import WsGeoDataset
from fiona.errors import DriverError


class PrecipitationDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, input_stationfile: str = "../assets/inputs/precipitation/precipitation_stations.shp",
                 input_datafile: str = "../assets/inputs/precipitation/precipitation_data.csv",
                 year_start: int = 2014):
        """ The initialization of the PrecipitationDataset class automatically scrapes the monthly precipitation data
        for the state of California in the data_df dataframe and downloads the weather's station location into the
        map_df dataframe.

        :param input_stationfile: the path to the CSV file containing the station dataIf it does not exists, the data
        will be scrapped from the web and stored into this file.
        :param input_datafile: the path to the CSV file containing the additional data dataset. If it does not exists,
        the data will be scrapped from the web and stored into this file.
        :param year_start: The year to start collecting the data from.
        :param year_end: The year to end collecting the data from.
        """
        self.year_start = year_start
        self.year_end = datetime.now().year - 1
        self.input_geofile = input_stationfile
        self.input_datafile = input_datafile
        # Try to load the dataset for pre-downloaded files. If not scrap the data from the web and save them
        try:
            WsGeoDataset.__init__(self, input_geofiles=[input_stationfile], input_datafile=input_datafile,
                                  merging_keys=["STATION_ID", "STATION_ID"])
        except (FileNotFoundError, DriverError):
            # Initialize the parent class with the bare minimum, without loading any data from file (outside of the
            # San Joaquin Valley Township data) as the data are scrapped from the web.
            WsGeoDataset.__init__(self, input_geofiles=[], merging_keys=["STATION_ID", "STATION_ID"])
            # Scrap the precipitation data and the precipitation geospatial data from the web
            self.data_df = self._get_monthly_precipitation_data()
            self.map_df = self._get_stations_geospatial_data()

    def _scrape_precipitation_data_per_year(self, year: int) -> pd.DataFrame:
        """This function downloads the precipitation data for a given year from the web and returns it as a dataframe.

        :param year: the year to download the data from.
        :return: the dataframe containing the precipitation data for the given year.
        """
        # The URL for the data for a given year
        url = f"https://cdec.water.ca.gov/reportapp/javareports?name=PRECIPMON.{year}"
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")
        precipitation_table = soup.find("table", attrs={"id": "data", "class": "data"})

        if precipitation_table is None:
            return pd.DataFrame()

        precipitation_table_header = precipitation_table.thead.find_all("th")
        precipitation_table_header = [th.text for th in precipitation_table_header]
        precipitation_table_header = precipitation_table_header[1:]
        precipitation_table_rows = precipitation_table.find_all('tr')
        all_rows_list = []
        for eachTableRow in precipitation_table_rows:
            this_row = []
            for td in eachTableRow.find_all("td"):
                this_row.append(td.text.strip())

            if this_row and len(this_row) > 1:
                all_rows_list.append(this_row)

        df = pd.DataFrame(all_rows_list)
        df.columns = precipitation_table_header
        months = ['OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP']
        for col in months:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['AVERAGE_YEARLY_PRECIPITATION'] = df[months].mean(axis='columns')
        df['YEAR'] = year
        df.rename(columns={"STATION ID": "STATION_ID", "STATION NAME": "STATION_NAME"}, inplace=True)
        df.drop(columns=months, inplace=True)
        return df

    def _get_monthly_precipitation_data(self):
        """This function loops through a set of years in a list, scrap the monthly precipitation from the
        California Dta Exchange Center web sites and computes the average yearly precipitation.

        :return: A dataframe containing the average yearly precipitation for all precipitation stations in California
        """
        all_years_precipitation_data = pd.DataFrame()
        # We use threading to load the data in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_year = executor.map(self._scrape_precipitation_data_per_year,
                                          range(self.year_start, self.year_end + 1))
        for year_df in future_to_year:
            if not year_df.empty:
                all_years_precipitation_data = pd.concat([all_years_precipitation_data, year_df], axis=0)
        all_years_precipitation_data.reset_index(drop=True, inplace=True)
        # Save the file for future direct loading
        all_years_precipitation_data.to_csv(self.input_datafile, index=False)
        return all_years_precipitation_data

    def _scrape_precipitation_station_data(self, level: str, station_features: List[str]):
        """This function scrapes the web for daily or monthly precipitation station data in order to retrieve all
        the weather station geospatial information.

        :param level: the level ("daily" ot "monthly") at which to gather precipitation data in order to extract the
        geospatial data of the stations
        :return: the precipitation stations geospatial data
        """
        if level == "daily":
            url = f"https://cdec.water.ca.gov/reportapp/javareports?name=DailyStations"
        else:
            url = "https://cdec.water.ca.gov/reportapp/javareports?name=MonthlyPrecip"
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")

        if level == "daily":
            station_table = soup.find("table", attrs={"id": "DLY_STNLIST", "class": "data"})
        else:
            station_table = soup.find("table", attrs={"id": "REALPRECIP_LIST", "class": "data"})

        all_rows_list = []
        for eachRow in station_table.find_all("tr"):
            this_row = []
            for td in eachRow.find_all("td"):
                this_row.append(td.text.strip())

            if this_row and len(this_row) > 1:
                all_rows_list.append(this_row)
        station_table = pd.DataFrame(all_rows_list)
        station_table.columns = station_table.iloc[0, :]
        station_table = station_table.iloc[2:, :].copy()
        station_table.rename(columns={"ID": "STATION_ID"}, inplace=True)
        station_table.drop(columns=["ELEV(FEET)"], inplace=True)
        station_table = station_table[station_features]
        return station_table

    def _get_stations_geospatial_data(self):
        """This function retrieves all the precipitation stations geospatial data. It scraps the web for precipitation
        data at daily and monthly level and extracts the latitude and longitude of all stations and returns it in a
        Geospatial dataframe.

        :return: The geospatial dataframe containing the latitude and longitude of all weather stations in California
        """
        station_features = ["STATION", "STATION_ID", "LATITUDE", "LONGITUDE", "COUNTY"]
        daily_station_data = self._scrape_precipitation_station_data("daily", station_features)
        monthly_station_data = self._scrape_precipitation_station_data("monthly", station_features)

        all_stations_data = pd.concat([daily_station_data, monthly_station_data], axis=0)
        all_stations_data = all_stations_data.groupby(station_features).agg(
            count_latitude=('LATITUDE', 'count')).reset_index()
        all_stations_data.drop(columns=["count_latitude"], inplace=True)
        all_stations_geodf = gpd.GeoDataFrame(
            all_stations_data,
            geometry=gpd.points_from_xy(
                all_stations_data.LONGITUDE,
                all_stations_data.LATITUDE
            ),
            crs="epsg:4326")
        # Save the file for future direct loading
        all_stations_geodf.to_file(self.input_geofile, index=False)
        return all_stations_geodf
