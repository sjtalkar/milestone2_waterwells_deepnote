import altair as alt
import pandas as pd
import geopandas as gpd
from datetime import datetime
from typing import List

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

def get_base_map(gdf: gpd.GeoDataFrame, color: str, opacity: float):
    """This function creates and returns an base map with Altair from the GeoDataFrame

    :param gdf: The geopandas DataFrame from which to generate the Altair base map
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

def get_stations_chart(stations_gdf: gpd.GeoDataFrame, tooltip_columns: List[str]):
    """This function creates and returns an Altair chart of the stations

    :param stations_gdf: The GeoDataFrame containing the stations data
    :param tooltip_columns: The columns to display in the tooltip
    """
    if "points" in list(stations_gdf.columns):
        points_df = stations_gdf.copy()
        points_df.drop(columns=["geometry"], inplace=True)
        points_df.set_geometry("points", inplace=True)
        stations_chart = alt.Chart(points_df).mark_geoshape().encode(
            color=alt.value('green'),
            tooltip=tooltip_columns,
        )
    else:
        stations_chart = alt.Chart(stations_gdf).mark_circle().encode(
            latitude='LATITUDE:Q',
            longitude='LONGITUDE:Q',
            tooltip=tooltip_columns,
            fill=alt.value('green'),
        )
    return stations_chart
      
def view_year_with_slider(base_map, gdf: gpd.GeoDataFrame, color_col: str, color_scheme : str = 'blues',
                          time_col: str = 'YEAR', draw_stations: bool =False):
    """This function generates an interactive visualization of the data with a slider

    :param base_map: The Altair chart to use as the base map
    :param gdf: The GeoDataFrame containing the data
    :param color_col: The column to use for the color
    :param color_scheme: The color scheme to use for the areas
    :param time_col: The column to use for the time
    :param draw_stations: If True, draw the stations
    """
    gdf = gdf.set_crs('epsg:4326')
    #Limit the time range so that the chart can be shown
    gdf = gdf[gdf[time_col] >= 2014]
    min_year_num = gdf[time_col].min()
    max_year_num = gdf[time_col].max()
    tooltip_columns = list(set(gdf.columns) - {"geometry", "points"})
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
    area_slider_chart = alt.Chart(gdf).mark_geoshape().encode(
        color=alt.Color(f'{color_col}', scale=alt.Scale(scheme=color_scheme)),
        tooltip=tooltip_columns
    ).transform_filter(
        slider_selection
    ).add_selection(
        slider_selection
    ).properties(
        width=500,
        height=500
    )

    if draw_stations:
        stations_chart = get_stations_chart(gdf, ['LONGITUTDE:Q', 'LATITUDE:Q'])
        return base_map + area_slider_chart + stations_chart
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
    area_df = gdf.copy()
    if "points" in list(area_df.columns):
        area_df.drop(columns=['points'], inplace=True)
    if year:
        area_df = area_df[area_df['YEAR'] == year]
    area_df['YEAR'] = area_df['YEAR'].astype(str)
    if area_df[feature].dtype == 'object':
        feature = f"{feature}:N"
    else:
        feature = f"{feature}:Q"
    tooltip_columns = list(set(area_df.columns) - {"geometry", "points"})
    if draw_stations:
        base = alt.Chart(area_df)
        feature_chart = base.mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(feature, scale=alt.Scale(scheme=color_scheme)),
            tooltip=tooltip_columns,
        ).properties(
            width=850,
            height=850,
            title=title
        )
        stations_chart = get_stations_chart(gdf, tooltip_columns)
        chart = feature_chart + stations_chart
        chart.properties(title=title)
    else:
        chart = alt.Chart(area_df).mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(feature, scale=alt.Scale(scheme=color_scheme)),
            tooltip=tooltip_columns,
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
    area_df = gdf.copy()
    if "points" in list(area_df.columns):
        area_df.drop(columns=['points'], inplace=True)
    area_df['YEAR'] = area_df['YEAR'].astype(str)
    tooltip_columns = list(set(area_df.columns) - {"geometry", "points"})
    if draw_stations:
        base = alt.Chart(area_df).mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(f'{feature}:Q', scale=alt.Scale(scheme=color_scheme)),
            tooltip=tooltip_columns,
        ).properties(
            width=350,
            height=350
        )
        stations_chart = get_stations_chart(gdf, tooltip_columns)
        chart = alt.layer(base, stations_chart, data=area_df).facet(
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
                    color=alt.Color(f'{feature}:Q', scale=alt.Scale(scheme=color_scheme)),
                    tooltip=tooltip_columns
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


def display_data_on_map(gdf: gpd.GeoDataFrame, feature: str = None, year: int = None):
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

def draw_corr_heatmap( df:pd.DataFrame,
                       drop_columns:list
):
    """
    Function to generate a heatmap for a dataframe
    
    :params df   : pd.Dataframe Dataframe with features
    :param drop_columns: Category columns that are not included in the correlation map
    :return    Altair heatmap chart
      
    """
    
    alt.data_transformers.disable_max_rows()
   
    cor_data = (df.drop(columns=drop_columns)
              .corr().stack()
              .reset_index()     # The stacking results in an index on the correlation values, we need the index as normal columns for Altair
              .rename(columns={0: 'correlation', 'level_0': 'feature_1', 'level_1': 'feature_2'}))
    cor_data['correlation_label'] = cor_data['correlation'].map('{:.2f}'.format)  # Round to 2 decimal
    
    base = (
        alt.Chart(cor_data)
              .encode(x= alt.X("feature_1:N", 
                          #sort=neworder
                     ),
                     y=alt.Y("feature_2:N",
                        #sort = neworder
                     ),
                     tooltip=[alt.Tooltip("feature_1:N", title='feature_1'),
                             alt.Tooltip("feature_2:N", title='feature_2'),
                             alt.Tooltip("correlation_label:Q", title='Correlation Value')
                             ]
               ).properties(width=alt.Step(10), height=alt.Step(10))
    )


    rects = (base.mark_rect().encode(
                            color=  alt.Color('correlation_label:Q',
                                              scale=alt.Scale(scheme ="lightgreyteal"))
                            ).properties(width=1000, height=1000)
            )
        
    return(rects)