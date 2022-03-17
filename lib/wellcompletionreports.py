import json
import pandas as pd
import geopandas as gpd

from typing import List, Tuple, Dict
from wsdatasets import WsGeoDataset

class WellCompletionReportsDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_geofiles: List[str] = ["../assets/inputs/common/plss_subbasin.geojson"],
                 input_datafile: str = "../assets/inputs/wellcompletion/wellcompletion.csv",
                 ):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles, input_datafile=input_datafile)
                              


    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        return pd.read_csv(input_datafile)

    def clean_well_completion_reports(self):
        wellcompletion_df = self.data_df

        #There are latitudes and longitudes that are corrupt : 37/41/11.82/
        wellcompletion_df = wellcompletion_df[~wellcompletion_df.DECIMALLATITUDE.str.contains(r"/", na=False)].copy()
        wellcompletion_df = wellcompletion_df[~wellcompletion_df.DECIMALLONGITUDE.str.contains(r"/", na=False)].copy()

        wellcompletion_df['DECIMALLATITUDE'] = wellcompletion_df.DECIMALLATITUDE.astype('float')
        wellcompletion_df['DECIMALLONGITUDE'] = wellcompletion_df.DECIMALLONGITUDE.astype('float')


        #Correct incorrectly signed logitude and latiude Example :   120.54483 Longitude
        wellcompletion_df['DECIMALLONGITUDE'] = np.where(wellcompletion_df['DECIMALLONGITUDE'] > 0,
                                                        -wellcompletion_df['DECIMALLONGITUDE'],
                                                        wellcompletion_df['DECIMALLONGITUDE'])

        wellcompletion_df['DECIMALLATITUDE'] = np.where(wellcompletion_df['DECIMALLATITUDE'] < 0,
                                                        -wellcompletion_df['DECIMALLATITUDE'],
                                                        wellcompletion_df['DECIMALLATITUDE'])

        #About 5% of the dataframe has eith latitude or longitude missing, we drop these
        wellcompletion_df = wellcompletion_df.dropna(subset=['DECIMALLATITUDE', 'DECIMALLONGITUDE']).copy()

        # Pick data of interest
        wellcompletion_subset_df = wellcompletion_df[["DECIMALLATITUDE", "DECIMALLONGITUDE", "TOWNSHIP", "RANGE", "SECTION", "WELLLOCATION", "CITY", "COUNTYNAME", 
                                                    "BOTTOMOFPERFORATEDINTERVAL", "TOPOFPERFORATEDINTERVAL", "GROUNDSURFACEELEVATION", "STATICWATERLEVEL", 
                                                    "RECORDTYPE",  "PLANNEDUSEFORMERUSE", "WCRNUMBER", "TOTALDRILLDEPTH", 
                                                    "TOTALCOMPLETEDDEPTH", "DATEWORKENDED", 'WELLYIELD', 'WELLYIELDUNITOFMEASURE']].copy()



        #len(wellcompletion_subset_df[(wellcompletion_subset_df['LATITUDE'].isnull()) | (wellcompletion_subset_df['LATITUDE'].isnull())])/  len(wellcompletion_subset_df)
        #.05

        # rename columns
        wellcompletion_subset_df.rename(columns={"DECIMALLATITUDE" : "LATITUDE", 
                                                "DECIMALLONGITUDE" : "LONGITUDE", 
                                                "PLANNEDUSEFORMERUSE": "USE" ,       
                                                "COUNTYNAME" : "COUNTY", 
                                            }, inplace=True)

        # filter to only include new well completion since we predict on this
        wellcompletion_subset_df = wellcompletion_subset_df.loc[wellcompletion_subset_df['RECORDTYPE'] == 'WellCompletion/New/Production or Monitoring/NA']

        # filter to only include agriculture, domestic, or public wells
        #Data issues Agriculture is also denoted by "AG"
        wellcompletion_subset_df['USE'] = wellcompletion_subset_df['USE'].fillna("")
        wellcompletion_subset_df['USE'] = wellcompletion_subset_df['USE'].str.lower()
        wellcompletion_subset_df['USE'] = (
                                            np.where(wellcompletion_subset_df['USE'].str.contains("agri|irrigation"),
                                                    "Agriculture",
                                                    np.where(wellcompletion_subset_df['USE'].str.contains("domestic"),
                                                            "Domestic",
                                                            np.where(wellcompletion_subset_df['USE'].str.contains("indus|commerc"),
                                                            "Industrial",
                                                            np.where(wellcompletion_subset_df['USE'].str.contains("public"),
                                                                    "Public",
                                                                    "Other")
                                                            )
                                                    )
                                            ))
        wellcompletion_subset_df = wellcompletion_subset_df[wellcompletion_subset_df["USE"].isin(["Agriculture","Domestic","Public", "Industrial"])]

        wellcompletion_subset_df['TOTALCOMPLETEDDEPTH'] = pd.to_numeric(wellcompletion_subset_df['TOTALCOMPLETEDDEPTH'], errors="coerce")

        # removes depth data that are less than 20'
        wellcompletion_subset_df['TOTALCOMPLETEDDEPTH_CORRECTED'] = wellcompletion_subset_df['TOTALCOMPLETEDDEPTH'].apply(lambda x: x if x >= 20 else np.nan)
        # convert date work ended to datetime and filter to only include completed dates that are possible (not a future date) 
        wellcompletion_subset_df['DATEWORKENDED'] = pd.to_datetime(wellcompletion_subset_df['DATEWORKENDED'], errors='coerce')
        # convert date work ended to datetime and filter to only include completed dates that are possible (not a future date) 
        wellcompletion_subset_df['DATEWORKENDED'] = pd.to_datetime(wellcompletion_subset_df['DATEWORKENDED'], errors='coerce')
        wellcompletion_subset_df['DATEWORKENDED_CORRECTED'] = wellcompletion_subset_df['DATEWORKENDED'].apply(lambda x: x if x < datetime.now() else np.nan)
        # create simple year and month columns
        wellcompletion_subset_df['YEARWORKENDED'] = pd.DatetimeIndex(wellcompletion_subset_df['DATEWORKENDED_CORRECTED']).year
        wellcompletion_subset_df['MONTHWORKENDED'] = pd.DatetimeIndex(wellcompletion_subset_df['DATEWORKENDED_CORRECTED']).month
        
        self.wellcompletion_subset_df = wellcompletion_subset_df

        return wellcompletion_subset_df
      
    # def preprocess_map_df(self, features_to_keep: List[str] = ["YEAR", "CROP_TYPE", "geometry"],
    #                       get_crops_details: bool=False):
    #     """This function preprocesses the well completion reports dataset extracting 
    #         pertinent features. 

    #     :param features_to_keep: the list of features (columns) to keep.
    #     :param get_drops_details: whether to extract the crops data at the crop level instead of the crop class level.
    #     """
      

    def merge_data_plss(self):
        """  Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. In the well completion reports, we have columns for latitude and longitude.
            - A GeoDataFrame needs a shapely object.
            - We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.
            - Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.
        
            MOVE TO BASE CLASS?
        """

        df = self.wellcompletion_subset_df
        # create wells geodataframe
        wellcompletion_subset_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE))
        #Set the coordinate reference system (the projection that denote the axis for the points)
        wellcompletion_subset_gdf = wellcompletion_subset_gdf.set_crs('epsg:4326')

        # spatial join based on geometry
        wellcompletion_subset_plss = wellcompletion_subset_gdf.sjoin(self.map_df, how="left")

        # drop the ones that aren't in the san joaquin valley basin
        wellcompletion_subset_plss = wellcompletion_subset_plss.dropna(subset=['MTRS'])
        
        self.wellcompletion_subset_plss(self, "/assets/outputs/well_completion_clean.csv", index=False)
        self.wellcompletion_subset_plss = self.wellcompletion_subset_plss
        return wellcompletion_subset_plss 


        def draw_mising_data_chart(self):
            """
                This function charts the percentage missing data in the data file read in

                 MOVE TO BASE CLASS?
            """

            df = self.data_df
            percent_missing = df.isnull().sum() / len(wellcompletion_df)
            missing_value_df = pd.DataFrame({'column_name': df.columns,
                                            'percent_missing': percent_missing})
            missing_value_df.sort_values('percent_missing', ascending = False, inplace=True)

            sort_list = list(missing_value_df['column_name'])
            chart = alt.Chart(missing_value_df
                            ).mark_bar(
                                ).encode(
                            y =alt.Y("sum(percent_missing)", stack="normalize", axis=alt.Axis(format='%')),
                            x = alt.X('column_name:N', sort=sort_list),
                            color=alt.value("orange"),
                            tooltip = ['column_name', 'percent_missing']
                            )
            
            
            text = chart.transform_calculate(
                position = 'datum.percent_missing + 0.05 * datum.percent_missing / abs(datum.percent_missing)'
            ).mark_text(
                align='center', 
                fontSize=10,
                color='black'
            ).encode(
                y='position:Q',
                text=alt.Text('percent_missing:Q', format='.0%'),
            )
            return chart + text 
