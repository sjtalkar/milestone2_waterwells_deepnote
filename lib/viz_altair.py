import altair as alt
import pandas as pd

def draw_mising_data_chart(df: pd.DataFrame):
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
      
def view_attribute_per_year(base_map, gdf, color_col, color_scheme='blues',  time_col = 'YEAR', draw_stations=False):
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

    area_slider_chart =  alt.Chart(df).mark_geoshape(
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
        stations =  chart_stations(df)
        return  base_map + area_slider_chart + stations 
    else:
         return base_map + area_slider_chart


