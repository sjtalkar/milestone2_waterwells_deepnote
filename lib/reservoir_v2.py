import requests
import pandas as pd
import geopandas as gpd
import numpy as np

from bs4 import BeautifulSoup
from typing import List
from lib.wsdatasets import WsGeoDataset
from fiona.errors import DriverError


class ReservoirDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, input_stationfile: str = "../assets/inputs/reservoir/reservoir_stations.shp",
                 input_datafile: str = "../assets/inputs/reservoir/reservoir_data.csv",
                 year_start: int = 2018, year_end: int = 2022):
        """ The initialization of the ReservoirDataset class automatically scrapes the weekly reservoir data
        for the state of California in the data_df dataframe and downloads the reservoir station location into the
        map_df dataframe.

        :param input_stationfile: the path to the CSV file containing the station dataIf it does not exists, the data
        will be scrapped from the web and stored into this file.
        :param input_datafile: the path to the CSV file containing the additional data dataset. If it does not exists,
        the data will be scrapped from the web and stored into this file.
        """
        self.input_stationfile = input_stationfile
        self.input_datafile = input_datafile
        # Try to load the dataset for pre-downloaded files. If not scrap the data from the web and save them
        try:
            print("Loading local datasets. Please wait...")
            WsGeoDataset.__init__(self, input_geofiles=[input_stationfile], input_datafile=input_datafile,
                                  merging_keys=["STATION_ID", "STATION_ID"])
            print("Loading of datasets complete.")
        except (FileNotFoundError, DriverError):
            # Initialize the parent class with the bare minimum, without loading the reservoir stations geospatial
            # dataset.
            WsGeoDataset.__init__(self, input_geofiles=[], merging_keys=["STATION_ID", "STATION_ID"])
            # Scrape the reservoir data and the reservoir geospatial data from the web
            self.data_df = self._get_weekly_reservoir_data()
            self.map_df = self._get_reservoir_station_geospatial_data()
            print("Loading of datasets complete.")

    def _download_weekly_reservoir_geospatial_data(self):
        """This function downloads the weekly reservoir data from the web and returns it as a dataframe.

        :return: The dataframe containing the weekly reservoir data.
        """
        print("Scrapping reservoir geospatial data from the web. Please wait...")
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get("https://cdec.water.ca.gov/reportapp/javareports?name=DailyRes").text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")
        station_table = soup.find("table", attrs={"id": "DailyRes_LIST", "class": "data"})
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
        station_table.rename(columns={'ID': 'STATION_ID'}, inplace=True)
        station_table.drop(columns=['OPERATOR AGENCY'], inplace=True)
        return station_table

    def _get_reservoir_station_geospatial_data(self):
        """This function retrieves all the precipitation stations geospatial data. It scraps the web for precipitation
        data at daily and monthly level and extracts the latitude and longitude of all stations and returns it in a
        Geospatial dataframe.

        :return: The geospatial dataframe containing the latitude and longitude of all weather stations in California
        """
        station_table = self._download_weekly_reservoir_geospatial_data()
        all_stations_geodf = gpd.GeoDataFrame(
            station_table,
            geometry=gpd.points_from_xy(
                station_table.LONGITUDE,
                station_table.LATITUDE
            ),
            crs="epsg:4326")
        # Save the file for future direct loading
        all_stations_geodf.to_file(self.input_stationfile, index=False)
        return all_stations_geodf

    def _scrape_reservoir_data_per_date(self, a_date: str):
        print("Data not found locally.\nScrapping reservoir data from the web. Please wait...")
        url = f"https://cdec.water.ca.gov/reportapp/javareports?name=RES.{a_date}"
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")
        reservoir_table = soup.find("table", attrs={"id": "RES", "class": "data"})
        if reservoir_table is None:
            # Return an empty dataframe if there is no data for the given date
            data_table_df = pd.DataFrame()
        else:
            reservoir_table_header = reservoir_table.thead.find_all("th")
            reservoir_table_header = [th.text.strip() for th in reservoir_table_header]
            reservoir_table_header = [elm.strip() for elm in reservoir_table_header[1:]]
            reservoir_table_rows = reservoir_table.find_all('tr', {'class': 'white'})
            all_rows_list = []
            for eachTableRow in reservoir_table_rows:
                this_row = []
                for td in eachTableRow.find_all("td"):
                    this_row.append(td.text.strip())

                if this_row and len(this_row) > 1:
                    all_rows_list.append(this_row)
            # Form a data_table for the collection of weekly rows
            data_table_df = pd.DataFrame(all_rows_list)
            data_table_df['date'] = pd.to_datetime(f'{a_date}')
            data_table_df.columns = reservoir_table_header + ['date']
        return data_table_df

    def _get_weekly_reservoir_data(self):
        """This function retrieves all the reservoir data from the web and returns them as a dataframe.

        :return: The dataframe containing the weekly reservoir data.
        """
        all_years_reservoir_data = pd.DataFrame()
        # The API has no data prior 2018
        for year_start_date in ["2018-01-01", "2019-01-01", "2020-01-01", "2021-01-01", "2022-01-01"]:

            # inclusive controls whether to include start and end that are on the boundary. The default, “both”,
            # includes boundary points on either end.
            date_list = pd.date_range(year_start_date, periods=53, freq='W')
            date_list = [week_date.strftime("%Y%m%d") for week_date in date_list if
                         pd.to_datetime(week_date).year == pd.to_datetime(year_start_date).year]

            # Create a dataframe for all dates of a year
            full_year_dataframe = pd.DataFrame()
            for a_date in date_list:
                data_table_df = self._scrape_reservoir_data_per_date(a_date)
                if not data_table_df.empty:
                    full_year_dataframe = pd.concat([full_year_dataframe, data_table_df], axis=0)
            if full_year_dataframe.empty:
                continue
            # Combine this years data with past years
            if all_years_reservoir_data.empty:
                all_years_reservoir_data = full_year_dataframe
            else:
                all_years_reservoir_data = pd.concat([all_years_reservoir_data, full_year_dataframe], axis=0)
        all_years_reservoir_data.rename(columns={'% of Capacity': 'PCT_OF_CAPACITY'}, inplace=True)
        all_years_reservoir_data = all_years_reservoir_data[~all_years_reservoir_data['Reservoir Name'].
            str.contains('Total')].copy()
        # Add a year and month column
        all_years_reservoir_data['YEAR'] = all_years_reservoir_data.date.dt.year
        all_years_reservoir_data.rename(columns={'StaID': 'STATION_ID', 'Reservoir Name': 'RESERVOIR_NAME'},
                                        inplace=True)
        all_years_reservoir_data = all_years_reservoir_data[['STATION_ID', 'YEAR', 'PCT_OF_CAPACITY', 'RESERVOIR_NAME']]
        # Filter out values of "---  and convert values to float
        all_years_reservoir_data = all_years_reservoir_data[all_years_reservoir_data['PCT_OF_CAPACITY'] != '---']
        #all_years_reservoir_data.dropna(subset=['PCT_OF_CAPACITY'], inplace=True)
        all_years_reservoir_data['PCT_OF_CAPACITY'] = all_years_reservoir_data['PCT_OF_CAPACITY'].astype(float)
        # Average by station and year
        all_years_reservoir_data = all_years_reservoir_data.groupby(['STATION_ID', 'YEAR', 'RESERVOIR_NAME'],
                                                                    as_index=False).mean()
        all_years_reservoir_data.to_csv(self.input_datafile, index=False)
        return all_years_reservoir_data

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function keeps only the features in the features_to_keep list from the original geospatial data.

        :param features_to_keep: the list of features (columns) to keep."""
        self.map_df = self.map_df[features_to_keep].drop_duplicates()
