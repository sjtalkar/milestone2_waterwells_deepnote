import json
import pygeos
import datetime
import requests

import numpy as np
import pandas as pd
import geopandas as gpd

from bs4 import BeautifulSoup

from typing import List, Tuple, Dict
from lib.wsdatasets import WsGeoDataset


class PrecipitationDataset:
    """This class loads, processes the precipitation dataset 
       The range of years for which the data is to be collected  is captured in 

        year_start : e.g. '2013'
        year_end : e.g. '2023' This is one year beyond the range
        output_file_directory : directory to store both weekly and yearly granularity file e.g. = /work/milestone2_waterwells_deepnote/assets/outputs/precipitation
    
    """
    def __init__(self, year_start, year_end, output_file_directory):
            self.year_start = year_start
            self.year_end = year_end
            self.output_file_directory = output_file_directory
            
            
        
    def scrape_monthly_precipitation_data(self):
        """
            This function loops through a set of years in a list
            It creates URLS at yearly level for precipitation In each URL, the data is at monthly level
            It creates one dataframe containing precipitation data at monthly level for years for which we have data
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
            for col in ['OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR','APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP']:
                data_table[col] = pd.to_numeric(data_table[col], errors='coerce')
            data_table['AVERAGE_YEARLY_PRECIPITATION'] =  data_table[ ['OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR','APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP']].mean(axis='columns')
            data_table['YEAR'] = curr_year
            data_table.rename(columns = {'STATION ID':'STATION_ID'}, inplace=True)
        
            if all_years_precipitation_data.empty:
                    all_years_precipitation_data = data_table 
            else:
                    all_years_precipitation_data  = all_years_precipitation_data.append(data_table)

            #Store in instance of class
            self.all_years_precipitation_data = all_years_precipitation_data
        return all_years_precipitation_data


    def get_precipitation_station_data(self, level):
        """
                This function webscrapes monthly and daily precipitation collecting data.
                level: Used to construct URL for monthly or daily stations as well as to identify the table in the HTML
                returns: station_data
        """
        
        if level == 'daily':
            url=f"https://cdec.water.ca.gov/reportapp/javareports?name=DailyStations"
        else:
            url=  "https://cdec.water.ca.gov/reportapp/javareports?name=MonthlyPrecip"


        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text

        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")

        if level == 'daily':
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
        station_table =  station_table.iloc[2:,:].copy()
        station_table.rename(columns={'ID':'STATION_ID'}, inplace=True)
        station_table.drop(columns=['ELEV(FEET)'], inplace = True)

        if level == 'daily':
            self.daily_station_table = station_table
        else:
            self.monthly_station_table = station_table
        return station_table


    def save_precipitation_data(self, all_years_precipitation_station):
        """
                This function saves the output dataset into file specified 
        """
        self.all_years_precipitation_station.to_csv(fr"{self.output_file_directory}/precipitation_stations.csv", index=False)


    def retrieve_merge_precipitation_stations(self): 
        """
            This function combines all precipitation data from statations, reported at monthly level and combines it with station location data
        """
        all_years_precipitation_data = self.all_years_precipitation_data
        daily_station_table = self.daily_station_table
        monthly_station_table = self.monthly_station_table 

        full_station_table = daily_station_table.append(monthly_station_table)
        group_full_station_count_df = full_station_table.groupby(['STATION', 'STATION_ID','LATITUDE', 'LONGITUDE', 'COUNTY' ]).agg(count_latitude=('LATITUDE', 'count')).reset_index()
        #Making sure we do not have duplicates
        #group_full_station_count_df[group_full_station_count_df.station_id.str.contains('ASM|ATW|BFK|BAL|YSV')]
        group_full_station_count_df.drop(columns=['count_latitude'], inplace=True)

        all_years_precipitation_station = all_years_precipitation_data.merge(group_full_station_count_df, how='inner', left_on='STATION_ID', right_on='STATION_ID')
        all_years_precipitation_station.drop(columns=['STATION'], inplace=True)
        self.all_years_precipitation_station = all_years_precipitation_station

        self.save_precipitation_data(all_years_precipitation_station)

        return all_years_precipitation_station


