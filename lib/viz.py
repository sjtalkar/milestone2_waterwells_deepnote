import altair as alt
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import datetime

def draw_missing_data_chart(df: pd.DataFrame):
    """This function charts the percentage missing data in the data file read in

    :param df: The Pandas DataFrame for which to draw missing data
    """
    percent_missing = df.isnull().sum() / len(df)
    missing_value_df = pd.DataFrame({'column_name': df.columns,
                                     'percent_missing': percent_missing})
    missing_value_df.sort_values('percent_missing', ascending=False, inplace=True)

    sort_list = list(missing_value_df['column_name'])
    chart = alt.Chart(missing_value_df
                      ).mark_bar(
    ).encode(
        y=alt.Y("sum(percent_missing)", stack="normalize", axis=alt.Axis(format='%')),
        x=alt.X('column_name:N', sort=sort_list),
        color=alt.value("orange"),
        tooltip=['column_name', 'percent_missing']
    )

    text = chart.transform_calculate(
        position='datum.percent_missing + 0.05 * datum.percent_missing / abs(datum.percent_missing)'
    ).mark_text(
        align='center',
        fontSize=10,
        color='black'
    ).encode(
        y='position:Q',
        text=alt.Text('percent_missing:Q', format='.0%'),
    )
    return chart + text

def draw_base_map(gdf, color, opacity):
    """
        When provided with a geodataframe, the function creates and returns a base map

        :param gdf: The geopandas DataFrame for which to draw missing data
        :param color: Color for the area
        :param opacity: Opacity to apply to the color

    """
    base_gdf = gdf.set_crs('epsg:4326')

    #Set the class's base chart 
    return alt.Chart(base_gdf).mark_geoshape(
                        stroke='black',
                        strokeWidth=1
                    ).encode(
                        color= alt.value(color),
                        opacity=alt.value(opacity),
                    ).properties(
                        width=500,
                        height=500
                    )


def chart_stations(df):
    
    stations_df = df[['LATITUDE', 'LONGITUDE']].drop_duplicates()
    return alt.Chart(stations_df).mark_circle().encode( 
        latitude='LATITUDE:Q',    
        longitude='LONGITUDE:Q',
        tooltip = ['LATITUDE:Q', 'LONGITUDE:Q'],
        fill=alt.value('green'),
        stroke=alt.value('blue')
    )
      
def view_year_with_slider(base_map, gdf, color_col, color_scheme='blues',  time_col = 'YEAR', draw_stations=False):
    """
            This function charts out a geodataframe with a slider that controls the data in the dataframe by the position of the slider indicating a Year period
            The color of the values is scaled by the color_col in the dataframe. MAKE SURE, the string contains type of column as well
 
    """

    gdf = gdf.set_crs('epsg:4326')
    #Limit the time range so that the chart can be shown
    df = gdf[gdf[time_col] >= 2014]


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

    area_slider_chart = alt.Chart(df).mark_geoshape(
                                                ).encode( 
                                                    color= alt.Color(f'{color_col}', scale=alt.Scale(scheme=color_scheme)),
                                                    tooltip= list(df.columns)
                                                ).transform_filter(
                                                    slider_selection
                                                ).add_selection(
                                                    slider_selection
                                                ).properties( 

                                                    width=500,
                                                    height=500
                                                )

    if draw_stations:
        stations = chart_stations(df)
        return base_map + area_slider_chart + stations
    else:
        return base_map + area_slider_chart

def simple_geodata_viz(gdf: gpd.GeoDataFrame, feature:str, title: str, year: int = None, color_scheme:str = 'blues',
                       draw_stations: bool = False):
    """This function creates a simple visualization of a single feature of a geodataframe.

    :param gdf: the geodataframe to visualize
    :param feature: the feature to visualize
    :param title: the title of the visualization
    :param year: the year to visualize
    :param color_scheme: the color scheme to use for the visualization
    :param draw_stations: if True, the stations will be drawn on the map
    :return: the Altair visualization
    """
    if "points" in list(gdf.columns):
        area_df = gdf.drop(columns=['points'])
    else:
        area_df = gdf.copy()
    if year:
        area_df = area_df[area_df['YEAR'] == year]
    area_df['YEAR'] = area_df['YEAR'].astype(str)
    if area_df[feature].dtype == 'object':
        feature = f"{feature}:N"
    else:
        feature = f"{feature}:Q"
    if draw_stations:
        base = alt.Chart(area_df)
        feature_chart = base.mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(feature, scale=alt.Scale(scheme=color_scheme)),
            tooltip=list(area_df.columns),
        ).properties(
            width=850,
            height=850
        )
        stations_chart = base.mark_circle().encode(
            latitude='LATITUDE:Q',
            longitude='LONGITUDE:Q',
            fill=alt.value('green'),
        )
        chart = feature_chart + stations_chart
        chart.properties(title=title)
    else:
        chart = alt.Chart(area_df).mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(feature, scale=alt.Scale(scheme=color_scheme)),
            tooltip=list(area_df.columns),
        ).properties(
            width=850,
            height=850,
            title=title
        )
    return chart

def view_year_side_by_side(gdf: gpd.GeoDataFrame, feature: str, title: str, color_scheme: str = 'blues',
                           draw_stations: bool = False):
    """ This function creates a side by side Altair visualization of the data per year for a given feature

    :param gdf: the geodataframe to be visualized
    :param feature: the feature to be visualized
    :param title: the title of the visualization
    :param color_scheme: the color scheme to be used
    :param draw_stations: if True, the stations will be drawn on each sur chart
    :return: the Altair visualization
    """
    if "points" in list(gdf.columns):
        area_df = gdf.drop(columns=['points'])
    else:
        area_df = gdf.copy()
    area_df['YEAR'] = area_df['YEAR'].astype(str)
    if draw_stations:
        base = alt.Chart(area_df).mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(f'{feature}:Q', scale=alt.Scale(scheme=color_scheme)),
            tooltip=list(area_df.columns),
        ).properties(
            width=350,
            height=350
        )
        stations = alt.Chart().mark_circle().encode(
            latitude='LATITUDE:Q',
            longitude='LONGITUDE:Q',
            fill=alt.value('green'),
        )
        chart = alt.layer(base, stations, data=area_df).facet(
            facet='YEAR:N',
            columns=3,
            title=title
        )
    else:
        # There is a bug in Vega-Lite and simple facet charts don't work with GeoPandas
        # References
        # - Altair: https://github.com/altair-viz/altair/issues/2369
        # - Vega-Lite: https://github.com/vega/vega-lite/issues/3729
        chart = alt.concat(*(
                alt.Chart(area_df[area_df.YEAR == year]).mark_geoshape(stroke='darkgray').encode(
                    color=alt.Color(f'{feature}:Q', scale=alt.Scale(scheme=color_scheme))
                ).properties(
                    width=350, height=350,
                    title=year
                )
                for year in sorted(area_df["YEAR"].unique())
            ),
            columns=3
        ).properties(title=title)
    return chart


def visualize_seasonality_by_month(gdf: gpd.GeoDataFrame, feature: str):
    """ This function visualizes the seasonality of the data by month

    :param gdf: the geodataframe to visualize
    :param feature: the feature to visualize
    :return: the Altair visualization
    """
    viz_gdf = gdf.copy()
    viz_gdf["DATE"] = viz_gdf.apply(lambda row: datetime(row.YEAR, row.MONTH, 1), axis=1)
    chart = alt.Chart(viz_gdf[viz_gdf["YEAR"] >= 2000]).mark_bar().encode(
        y=f"{feature}:Q",
        x="DATE:T",
        tooltip=["YEAR", "MONTH", f"{feature}:Q"]
    ).properties(width=800)
    return chart


def display_data_on_map(gdf: gpd.GeoDataFrame, feature: str, year: int = None):
    """Use GeoPandas explore() function based on Folium to display the Geospatial data on a map.

    :param gdf: the GeoDataFrame to be displayed
    :param feature: the feature to be displayed
    :param year: the year to be displayed
    :return: the Folium map
    """
    if year:
        return gdf[gdf.YEAR == year].explore(feature)
    else:
        return gdf.explore(feature)