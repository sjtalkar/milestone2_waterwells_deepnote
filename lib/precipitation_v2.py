import requests

import pandas as pd
import geopandas as gpd

from bs4 import BeautifulSoup
from typing import List
from lib.wsdatasets import WsGeoDataset


class PrecipitationDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, year_start: int = 2013, year_end: int = 2022):
        """ The initialization of the PrecipitationDataset class automatically scrapes the monthly precipitation data
        for the state of California in the data_df dataframe and downloads the weather's station location into the
        map_df dataframe.

        :param year_start: The year to start collecting the data from.
        :param year_end: The year to end collecting the data from.
        """
        # Initialize the parent class with the bare minimum, without loading any data from file (outside of the
        # San Joaquin Valley Township data) as the data are scrapped from the web.
        WsGeoDataset.__init__(self, input_geofiles=[], merging_keys=["STATION_ID", "STATION_ID"])
        self.year_start = year_start
        self.year_end = year_end
        # Scrap the precipitation data and the precipitation geospatial data from the web
        self.data_df = self._scrape_monthly_precipitation_data()
        self.map_df = self._retrieve_stations_geospatial_data()

    def _scrape_monthly_precipitation_data(self):
        """This function loops through a set of years in a list, scrap the monthly precipitation from the
        California Dta Exchange Center web sites and computes the average yearly precipitation.

        :return: A dataframe containing the average yearly precipitation for all precipitation stations in California
        """
        all_years_precipitation_data = pd.DataFrame()
        for curr_year in range(self.year_start,self.year_end):
            url=f"https://cdec.water.ca.gov/reportapp/javareports?name=PRECIPMON.{curr_year}"

            # Make a GET request to fetch the raw HTML content
            html_content = requests.get(url).text
            # Parse the html content
            soup = BeautifulSoup(html_content, "lxml")
            precipitation_table = soup.find("table", attrs={"id":"data", "class": "data"})
        
            if precipitation_table is None:
                continue
            
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

            data_table = pd.DataFrame(all_rows_list )
            data_table.columns = precipitation_table_header
            months = ['OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR','APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP']
            for col in months:
                data_table[col] = pd.to_numeric(data_table[col], errors='coerce')
            data_table['AVERAGE_YEARLY_PRECIPITATION'] = data_table[months].mean(axis='columns')
            data_table['YEAR'] = curr_year
            data_table.rename(columns = {'STATION ID':'STATION_ID'}, inplace=True)
            data_table.drop(columns=months, inplace=True)
        
            if all_years_precipitation_data.empty:
                all_years_precipitation_data = data_table
            else:
                all_years_precipitation_data = pd.concat([all_years_precipitation_data, data_table], axis=0)
        return all_years_precipitation_data


    def _get_precipitation_station_data(self, level: str, station_features: List[str]):
        """This function scrapes the web for daily or monthly precipitation station data in order to retrieve all
        the weather station geospatial information.

        :param level: the level ("daily" ot "monthly") at which to gather precipitation data in order to extract the
        geospatial data of the stations
        :return: the precipitation stations geospatial data
        """
        if level == "daily":
            url=f"https://cdec.water.ca.gov/reportapp/javareports?name=DailyStations"
        else:
            url= "https://cdec.water.ca.gov/reportapp/javareports?name=MonthlyPrecip"

        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")

        if level == "daily":
            station_table = soup.find("table", attrs={"id":"DLY_STNLIST", "class": "data"})
        else:
            station_table = soup.find("table", attrs={"id":"REALPRECIP_LIST", "class": "data"})

        all_rows_list = []
        for eachRow in station_table.find_all("tr"):
            this_row = []
            for  td in eachRow.find_all("td"):
                this_row.append(td.text.strip())

            if this_row and len(this_row) > 1:
                all_rows_list.append(this_row)
        station_table = pd.DataFrame(all_rows_list )
        station_table.columns = station_table.iloc[0,:]
        station_table = station_table.iloc[2:,:].copy()
        station_table.rename(columns={"ID":"STATION_ID"}, inplace=True)
        station_table.drop(columns=["ELEV(FEET)"], inplace = True)

        return station_table[station_features]

    def _retrieve_stations_geospatial_data(self):
        """This function retrieves all the precipitation stations geospatial data. It scraps the web for precipitation
        data at daily and monthly level and extracts the latitude and longitude of all stations and returns it in a
        Geospatial dataframe.

        :return: The geospatial dataframe containing the latitude and longitude of all weather stations in California
        """
        station_features = ["STATION", "STATION_ID", "LATITUDE", "LONGITUDE", "COUNTY"]
        daily_station_data = self._get_precipitation_station_data("daily", station_features)
        monthly_station_data = self._get_precipitation_station_data("monthly", station_features)

        all_stations_data = pd.concat([daily_station_data, monthly_station_data], axis=0)
        all_stations_data = all_stations_data.groupby(station_features).agg(
            count_latitude=('LATITUDE', 'count')).reset_index()
        #Making sure we do not have duplicates
        #all_stations_data[all_stations_data.station_id.str.contains('ASM|ATW|BFK|BAL|YSV')]
        all_stations_data.drop(columns=["count_latitude"], inplace=True)
        all_stations_geodf = gpd.GeoDataFrame(
            all_stations_data,
            geometry=gpd.points_from_xy(
                all_stations_data.LONGITUDE,
                all_stations_data.LATITUDE
            ),
            crs="epsg:4326")
        return all_stations_geodf

    def preprocess_map_df(self):
        """This function keeps only the SITE_CODE, COUNTY and geometry features in the original geospatial data."""
        self.map_df = self.map_df[['STATION_ID','COUNTY','geometry']]




