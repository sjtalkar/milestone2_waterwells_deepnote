## This file contains functions common to charting datasets where a slider picks a time period and normalized data is 
## shown in the figure

import json
import pprint
import numpy as np
import pandas as pd
import altair as alt
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt



class NormalizedDataSliderVisualization:
        def __init__(self, area_geofile : str = '../assets/inputs/common/plss_subbasin.geojson',
                         base_geofile:str = 'https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/california-counties.geojson'):
           
            # this stores the California county map with couty boundaries as a base
            geo_json_file_loc = base_geofile
            base_gdf = gpd.read_file(geo_json_file_loc)
            base_gdf.set_crs('epsg:4326')

            #Set the class's base chart 
            self.county_base = alt.Chart(base_gdf).mark_geoshape(
                                stroke='black',
                                strokeWidth=1
                            ).encode(
                                color= alt.value('lightgray'),
                                opacity=alt.value(.3),
                            ).properties(
                                width=500,
                                height=500
                            )

            #This stores the San Joaquin River Basin a base geodataframe
            self.plss_gdf = gpd.read_file(area_geofile)
            self.plss_range = self.plss_gdf.dissolve(by='TownshipRange').reset_index()
                        



        def view_attribute_per_year(self, df, color_col='GSE_GWE_NORMALIZED', time_col = 'YEAR'):
            """
                    This function charts out a geodataframe with a slider that controls the data in the dataframe by the position of the slider indicating a Year period
                    The color of the values is scaled by the color_col in the dataframe

                    The df will have a geometry of points or polygons. But it is left joined with a dataframe with polygons and hence polygins will be charted 
            
            """
            #Limit the time range so that the chart can be shown
            df = df[df[time_col] >= 2014]
            #By left joining the plss dataframe we replace the poin
            df_poly = self.plss_range.sjoin(df)

            min_year_num = df[time_col].min()
            max_year_num = df[time_col].max()
            slider = alt.binding_range(
                min=min_year_num,
                max=max_year_num,
                step=1,
                name="Year: ",
            )

            slider_selection = alt.selection_single(
                fields=[f"{time_col}"], bind=slider, name="Year:",
                init={f"{time_col}": 2014}
            )

            self.area_slider_chart =  alt.Chart(  df_poly).mark_geoshape(
                                                        ).encode( 
                                                            color= alt.Color(f'{color_col}', scale=alt.Scale(scheme='purpleorange')),
                                                            tooltip= list(df_poly.columns)
                                                        ).transform_filter(
                                                            slider_selection
                                                        ).add_selection(
                                                            slider_selection
                                                        ).properties( 

                                                            width=500,
                                                            height=500
                                                        )
            return  self.county_base + self.area_slider_chart 


        def explore_data(self, df, year_column:str, color_column:str, year:int = 2021,):
            """
                    This function converts a poitn geometry dataframe into a polygon geometry dataframe by left joining a plss of san joaquin county
                    it then calls geopandas explore function
            """
            df = df[df[year_column] == year]

            df_poly = self.plss_range.sjoin(df)
            
            return df_poly.explore(color_column)


