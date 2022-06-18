import altair as alt
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import List
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap

sjv_brown = "#A9784F"
sjv_blue = "#3586BD"
sjv_error = "#DF77D1"
sjv_color_range_9 = ["#3586BD", "#4485B0", "#5283A2", "#618194", "#6F7F86", "#7E7E79", "#8C7C6B", "#9B7A5D", "#A9784F"]
sjv_color_range_17 =["#3586BD", "#3D86B7", "#4485B0", "#4B84A9", "#5283A2", "#5A829B", "#618194", "#68808D", "#6F7F86",
                     "#777F80", "#7E7E79", "#857D72", "#8C7C6B", "#947B64", "#9B7A5D", "#A27956", "#A9784F"]
sjv_cmap = LinearSegmentedColormap.from_list("sjv_cmap", [sjv_blue, sjv_brown])


def draw_missing_data_chart(df: pd.DataFrame):
    """This function charts the percentage missing data in the data file read in

    :param df: The Pandas DataFrame for which to draw missing data
    """
    percent_missing = df.isnull().sum() / len(df)
    missing_value_df = pd.DataFrame({'column_name': df.columns,
                                     'percent_missing': percent_missing})
    missing_value_df.sort_values('percent_missing', ascending=False, inplace=True)

    color_for_bars = '#6e0a1e' #'orange'

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
    :param feature: the name of the feature to visualize
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
    if "YEAR" in list(area_df.columns):
        area_df['YEAR'] = area_df['YEAR'].astype(str)
    # Set the color scale depending on the parameters
    if color_scheme == "sjv" or color_scheme == "sjv_with_error":
        color_scale = alt.Scale(range=[sjv_blue, sjv_brown])
        # If the variable is ordinal we extract the required number of colors
        nb_features = len(area_df[feature].unique())
        # If we want to reserve a color for error values we reduce the number of features by one
        if color_scheme == "sjv_with_error":
            nb_features -= 1
        if area_df[feature].dtype == 'object' and 2 < nb_features < len(sjv_color_range_17):
            color_range = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_features-1)]
            color_range[-1] = sjv_brown
            # If we want to reserve a color for error we add the error color at teh beginning
            # Negative values are error values
            if color_scheme == "sjv_with_error":
                color_range = [sjv_error] + color_range
            color_scale = alt.Scale(range=color_range)
    else:
        color_scale = alt.Scale(scheme=color_scheme)
    # Set the feature type
    if area_df[feature].dtype == 'object':
        feature = f"{feature}:N"
    else:
        feature = f"{feature}:Q"
    tooltip_columns = list(set(area_df.columns) - {"geometry", "points"})

    if draw_stations:
        base = alt.Chart(area_df)
        feature_chart = base.mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(feature, scale=color_scale),
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
            color=alt.Color(feature, scale=color_scale),
            tooltip=tooltip_columns,
        ).properties(
            width=850,
            height=850,
            title=title
        )
    return chart

def view_trs_side_by_side(gdf: pd.DataFrame, feature: str, value: str, title: str, color_scheme: str = 'blues',
                          draw_stations: bool = False):
    """ This function creates a side by side Altair visualization of the Township-Ranges for the given feature

    :param gdf: the geodataframe to be visualized
    :param feature: the name of the DataFrame column used for the small multiples facets
    :param value: the name of the DataFrame column containing the Township-Ranges values
    :param title: the title of the visualization
    :param color_scheme: the color scheme to be used
    :param draw_stations: if True, the stations will be drawn on each sur chart
    :return: the Altair visualization
    """
    area_df = gdf.copy()
    if "points" in list(area_df.columns):
        area_df.drop(columns=['points'], inplace=True)
    if area_df[feature].dtype != str:
        area_df[feature] = area_df[feature].astype(str)
    tooltip_columns = list(set(area_df.columns) - {"geometry", "points"})
    # Set the color scale depending on the parameters
    if color_scheme == "sjv" or color_scheme == "sjv_with_error":
        color_scale = alt.Scale(range=[sjv_blue, sjv_brown])
        # If the variable is ordinal we extract the required number of colors
        nb_values = len(area_df[value].unique())
        # If we want to reserve a color for error values we reduce the number of features by one
        if color_scheme == "sjv_with_error":
            nb_values -= 1
        if area_df[value].dtype == 'object' and 2 < nb_values < len(sjv_color_range_17):
            color_range = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_values-1)]
            color_range[-1] = sjv_brown
            # If we want to reserve a color for error we add the error color at teh beginning
            # Negative values are error values
            if color_scheme == "sjv_with_error":
                color_range = [sjv_error] + color_range
            color_scale = alt.Scale(range=color_range)
    else:
        color_scale = alt.Scale(scheme=color_scheme)
    # Set the feature type
    feature_name = value
    if area_df[value].dtype == 'object':
        value = f"{value}:N"
    else:
        value = f"{value}:Q"

    if draw_stations:
        base = alt.Chart(area_df).mark_geoshape(stroke='darkgray').encode(
            color=alt.Color(value, scale=color_scale,
                            legend=alt.Legend(title=feature_name, orient="bottom",
                                              labelFontSize=12, titleFontSize=14)),
            tooltip=tooltip_columns,
        ).properties(
            width=350,
            height=350
        )
        stations_chart = get_stations_chart(gdf, tooltip_columns)
        chart = alt.layer(base, stations_chart, data=area_df).facet(
            facet=f"{feature}:N",
            columns=3,
            title=title
        )
    else:
        # There is a bug in Vega-Lite and simple facet charts don't work with GeoPandas
        # References
        # - Altair: https://github.com/altair-viz/altair/issues/2369
        # - Vega-Lite: https://github.com/vega/vega-lite/issues/3729
        chart = alt.concat(*(
            alt.Chart(area_df[area_df[feature] == feature_]).mark_geoshape(stroke='darkgray').encode(
                color=alt.Color(value, scale=color_scale),
                tooltip=tooltip_columns
            ).properties(
                width=350, height=350,
                title=feature_
            )
            for feature_ in sorted(area_df[feature].unique())
        ),
                           columns=3
                           ).properties(title=title)
    return chart

def visualize_seasonality_by_month(gdf: gpd.GeoDataFrame, feature: List[str]):
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


def display_data_on_map(gdf: gpd.GeoDataFrame, feature: str, year: int = None, categorical: bool = False,
                        color_scheme: str = "viridis"):
    """Use GeoPandas explore() function based on Folium to display the Geospatial data on a map.

    :param gdf: the GeoDataFrame to be displayed
    :param feature: the feature to be displayed
    :param year: the year to be displayed
    :param categorical: whether the data are categorical or not
    :return: the Folium map
    """
    if color_scheme == "sjv":
        nb_categories = gdf[feature].unique()
        if categorical and 2 < len(nb_categories) < len(sjv_color_range_17):
            cmap = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_categories-1)]
            cmap[-1] = sjv_brown
        if categorical and len(nb_categories) == 2:
            cmap = [sjv_blue, sjv_brown]
        else:
            cmap = sjv_cmap
    else:
        cmap = color_scheme
    if year:
        return gdf[gdf.YEAR == year].explore(feature, cmap=cmap)
    else:
        return gdf.explore(feature, cmap=cmap)

def draw_corr_heatmap(df: pd.DataFrame, drop_columns: List[str] = None):
    """
    Function to generate a heatmap for a dataframe
    
    :params df   : pd.Dataframe Dataframe with features
    :param drop_columns: Category columns that are not included in the correlation map
    :return    Altair heatmap chart
      
    """
    
    alt.data_transformers.disable_max_rows()
    if drop_columns:
        chart_df = df.drop(columns=drop_columns)
    else:
        chart_df = df
   
    cor_data = (chart_df.corr().stack()
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


def draw_components_variance_chart(
    pca
):
    """
    This function creates a scree plot. A scree plot plots the explained variance against number of components
    and helps determine the number of components to pick.

    params: pca: pca object fit to the data
    returns:  Dataframe with NaNs replaced for vegetation and crops columns
    """
    
    
    df = pd.DataFrame({'n_components' : range(1,pca.n_components_ + 1), 'explained_variance':pca.explained_variance_ratio_})
    
    return alt.Chart(df
    ).mark_line(
    ).encode(
    x='n_components:O',
    y='explained_variance:Q')


def biplot(score, coeff, maxdim, pcax, pcay, labels=None):
    """
      This function uses 
      score - the transformed data returned by pca - data as expressed according to the new axis
      coeff - the loadings from the pca_components_
      
      For the feaures we are interested in, it plots the correlation between the original features and the PCAs.
      Use cosine similarity and angle measures between axes.
      
      It shows how the data is related to the ORIGINAL features in the positive and negative direction.

      :param: score is the value of data points as per the linear combination of the principal axes
      :param:coeff: are the eigen values of the eigen vectors
      :param:pcax: The horizontal X-axis
      :param:pcay: The vertical y-axis 
      
    """
    zoom = 0.5
    pca1=pcax-1
    pca2=pcay-1
    xs = score[:,pca1]
    ys = score[:,pca2]
    n = min(coeff.shape[0], maxdim)
    width = 2.0 * zoom
    scalex = width/(xs.max()- xs.min())
    scaley = width/(ys.max()- ys.min())
    text_scale_factor = 1.3
        
    fig = plt.gcf()
    #fig.set_size_inches(9, 9)
    fig.set_size_inches(16, 16)
    
    
    plt.scatter(xs*scalex, ys*scaley, s=9)
    for i in range(n):
        plt.arrow(0, 0, coeff[i,pca1], coeff[i,pca2],
                  color='b',alpha=0.9, head_width = 0.03 * zoom) 
        if labels is None:
            plt.text(coeff[i,pca1]* text_scale_factor, 
                     coeff[i,pca2] * text_scale_factor, 
                     "Var"+str(i+1), color='g', ha='center', va='center')
        else:
            plt.text(coeff[i,pca1]* text_scale_factor, 
                     coeff[i,pca2] * text_scale_factor, 
                     labels[i], color='g', ha='center', va='center')
    
    plt.xlim(-zoom,zoom)
    plt.ylim(-zoom,zoom)
    plt.xlabel("PC{}".format(pcax))
    plt.ylabel("PC{}".format(pcay))
    plt.grid()
    return plt

def draw_feature_importance(feature_list: list, importance_list: list):
    """This function charts the percentage missing data in the data file read in

    :param feature_list: The list of features for which the regressor provides importance values
    :param importance_list: Values of feature importance

    """
    df = pd.DataFrame({"Feature Name": feature_list, "Importance": importance_list})
    feature_imp_chart = (
        alt.Chart(df)
        .mark_bar(color="#6e0a1e")
        .encode(x=alt.X("Feature Name:N", sort="-y"), y="Importance:Q")
    )
    return feature_imp_chart

def draw_histogram(df: pd.DataFrame, col_name:str ):
    """This function charts the percentage missing data in the data file read in

    :param df: Dataframe in which resides the column for which histogram is to be plotted
    :param col_name: Name of column for which histogram is to be plotted
    """
    x_mean = np.round(df[col_name].mean(), 2)
    x_median = np.round(df[col_name].median(), 2)
    base = alt.Chart(df)

    mean_df = pd.DataFrame({'x': [x_mean, x_median], 'y':[1000, 1100], 'value':[f"Mean = {x_mean}", f"Median = {x_median}"]})

    txt_chart = alt.Chart(mean_df).mark_text(
        align='left', 
        fontSize=15,
        color="black"
    ).encode(
        y='y:Q',
        text=alt.Text('value:N'),
    )

    hist = base.mark_bar(color="#6e0a1e").encode(
                    alt.X(f"{col_name}:Q", bin=True),
                    y='count()',
                )
    return (txt_chart + hist).configure_axis( grid=False )

def draw_two_lines_with_two_axis(df: pd.DataFrame, x:str, y1:str, y2:str,
                                 title: str, x_title: str, y1_title: str, y2_title):
    """This function plots two lines on the same chart with independant y-axis
    :param df: the Dataframe with the data to be plotted
    :param x: the column name of the x-axis
    :param y1: the column name of the first line
    :param y2: the column name of the second line
    :param title: the title of the chart
    :param x_title: the title of the x-axis
    :param y1_title: the title of the first line
    :param y2_title: the title of the second line
    :return: the Altair visualization
    """
    x_values = list(df[x].values)
    base = alt.Chart(df).encode(
        x=alt.X(x, axis=alt.Axis(title=x_title, values=x_values))
    )
    y1_line = base.mark_line(color=sjv_brown).encode(
        y=alt.Y(y1, axis=alt.Axis(title=y1_title, titleColor=sjv_brown, titleAngle=0, titlePadding=50)),
    )
    y2_line = base.mark_line(color=sjv_blue).encode(
        y=alt.Y(y2, axis=alt.Axis(title=y2_title, titleColor=sjv_blue, titleAngle=0, titlePadding=55)),
    )
    chart = (y1_line + y2_line).resolve_scale(y="independent")
    if title:
        chart = chart.properties(title=title)
    return chart

def draw_faceted_two_lines_with_two_axis(df: pd.DataFrame, x:str, y1:str, y2:str, facet: str,
                                         title: str, x_title: str, y1_title: str, y2_title, facet_titles: List[str]):
    """This function plots a chart of two lines on the same chart with independent y-axis, for each value in the
    facet variable

    :param df: the Dataframe with the data to be plotted
    :param x: the column name of the x-axis
    :param y1: the column name of the first line
    :param y2: the column name of the second line
    :param facet: the column name of the facet variable
    :param title: the title of the chart
    :param x_title: the title of the x-axis
    :param y1_title: the title of the first line
    :param y2_title: the title of the second line
    :return: the Altair visualization
    """
    for i, facet_value in enumerate(list(df[facet].unique())):
        chart_df = df[df[facet] == facet_value]
        if i == 0:
            chart = draw_two_lines_with_two_axis(chart_df, x=x, y1=y1, y2=y2, title=facet_titles[i], x_title=x_title,
                                                 y1_title=y1_title, y2_title=y2_title)
        else:
            chart |= draw_two_lines_with_two_axis(chart_df, x=x, y1=y1, y2=y2, title=facet_titles[i], x_title=x_title,
                                                  y1_title=y1_title, y2_title=y2_title)
    chart = chart.properties(title=title)
    return chart

def draw_faceted_lines(df: pd.DataFrame, x:str, y:str, facet: str, title: str, x_title: str, y_title: str):
    """This function plots a facet line-chart on the same chart with independent y-axis, for each value in the
    facet variable

    :param df: the Dataframe with the data to be plotted
    :param x: the column name of the x-axis
    :param y: the column name of the y-axis
    :param facet: the column name of the facet variable
    :param title: the title of the chart
    :param x_title: the title of the x-axis
    :param y_title: the title of the y-axis
    :return: the Altair visualization
    """
    x_values = list(df[x].values)
    # extract 1 color per facet from the custom sjv_color_range_17 color list
    # at regular intervals
    nb_facets = len(df[facet].unique())
    if nb_facets > 2 and nb_facets < len(sjv_color_range_17):
        color_range = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_facets-1)]
        color_range[-1] = sjv_brown
    else:
        color_range = [sjv_blue, sjv_brown]
    chart = alt.Chart(df).mark_line().encode(
        x=alt.X(
            x,
            axis=alt.Axis(title=x_title, values=x_values)
        ),
        y=alt.Y(
            y,
            axis=alt.Axis(
                title=y_title,
                titleAngle=0,
                titlePadding=50)
        ),
        color=alt.Color(
            f"{facet}:N",
            scale=alt.Scale(range=color_range),
            legend=None
        ),
    ).facet(
        facet=alt.Facet(
            f"{facet}:N",
            header=alt.Header(title=None)
        ),
        columns=2
    ).resolve_scale(y="independent").properties(title=title)
    return chart

def draw_small_multiples_bar_charts(df: pd.DataFrame, x:str, y:str, facet: str, facet_sort: List[str], title:str):
    """This function generate small multiples bar charts

    :param df: the Dataframe with the data to be plotted
    :param x: the column name of the x-axis
    :param y: the column name of the y-axis
    :param facet: the column name of the facet variable
    :param facet_sort: the order of the facet values
    :param title: the title of the chart
    """
    # extract 1 color per facet from the custom sjv_color_range_17 color list
    # at regular intervals
    nb_x = len(df[x].unique())
    if 2 < nb_x < len(sjv_color_range_17):
        color_range = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_x-1)]
        color_range[-1] = sjv_brown
    else:
        color_range = [sjv_blue, sjv_brown]
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x}:N", axis=None),
        y=alt.Y(f"{y}:Q", axis=alt.Axis(grid=False)),
        color=alt.Color(f"{x}:N", scale=alt.Scale(range=color_range)),
    ).facet(
        facet=alt.Facet(
            f"{facet}:N",
            sort=facet_sort,
            header=alt.Header(title=None, labelOrient="bottom")
        ),
        columns=5,
        spacing={"row": 30, "column": -10},
    ).properties(title=title).configure_view(stroke="transparent")
    return chart

def draw_hierarchical_parameters_results(df: pd.DataFrame, x:str, y:str, facet: str, title: List[str], x_title: str,
                                         y_title: str, nb_facet_columns: int = 2):
    """This function plots a faceted line chart for the results of the hierarcical clustering parameters search results

    :param df: the Dataframe with the data to be plotted
    :param x: the column name of the x-axis
    :param y: the column name of the y-axis
    :param facet: the column name of the facet variable
    :param title: the title of the chart
    :param x_title: the title of the x-axis
    :param y_title: the title of the y-axis
    :param nb_facet_columns: the number of columns in the facet
    :return: the Altair visualization
    """
    x_values = list(df[x].values)
    # extract 1 color per facet from the custom sjv_color_range_17 color list
    # at regular intervals
    nb_facets = len(df[facet].unique())
    if nb_facets > 2 and nb_facets < len(sjv_color_range_17):
        color_range = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_facets-1)]
        color_range[-1] = sjv_brown
    else:
        color_range = [sjv_blue, sjv_brown]
    chart = alt.Chart(df).mark_line().encode(
        x=alt.X(
            x,
            sort="y",
            axis=alt.Axis(title=x_title, values=x_values, labelAngle=-45, labelAlign="right")
        ),
        y=alt.Y(
            y,
            axis=alt.Axis(
                title=y_title,
                titleAngle=0,
                titlePadding=50)
        ),
        color=alt.Color(
            f"{facet}:N",
            scale=alt.Scale(range=color_range),
            legend=None
        ),
    ).facet(
        facet=alt.Facet(
            f"{facet}:N",
            header=alt.Header(title=None)
        ),
        columns=nb_facet_columns
    ).resolve_scale(x="independent", y="independent").properties(title=title)
    return chart