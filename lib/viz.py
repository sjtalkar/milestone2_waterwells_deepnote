import math
import altair as alt
import math
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.cm as cm
from typing import List
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.cluster import KMeans

sjv_brown = "#A9784F"
sjv_pink = "#AF6A9A"
sjv_blue = "#3586BD"
sjv_error = "#E24C85"
sjv_color_range_9 = ["#3586BD", "#547FB5", "#7278AC", "#9171A3", "#AF6A9A", "#AE6E88", "#AC7175", "#AB7562", "#A9784F"]
sjv_color_range_17 = ["#3586BD", "#4583B9", "#547FB5", "#637CB1", "#7278AC", "#8275A8", "#9171A3", "#A06E9F", "#AF6A9A",
                      "#AF6C91", "#AE6E88", "#AD707F", "#AC7175", "#AC736C", "#AC736C", "#AA7759", "#A9784F"]
sjv_cmap = LinearSegmentedColormap.from_list("sjv_cmap", list(zip([0.0, 0.5, 1.0], [sjv_blue, sjv_pink, sjv_brown])))
sjv_cmap.set_bad(sjv_error)


def create_feature_target_heatmap(full_df: pd.DataFrame(), target: str, sort_by_absolute: bool):
    """This function plots features to target correlation heatmap using seaborn

    :param full_df: Dataframe containing feature and target columns
    :param target: name of target column in dataframe
    :param: sort_by_absolute: Flag True/False indicating if the sorting must be performed using 'absolute'
    value of correlation
    :returns: a Seaborn heatmap
    """
    corr_df = full_df.corr()[[target]].copy()
    plt.figure(figsize=(8, 30))
    color_map = sjv_cmap
    
    if sort_by_absolute:
        corr_df['sort_by_value'] = np.abs(corr_df[target])
        corr_df.sort_values(by='sort_by_value', ascending=False, inplace=True)
        corr_df.drop(columns=['sort_by_value'], inplace=True)
        heatmap = sns.heatmap(corr_df, vmin=-1, vmax=1, annot=True, cmap=color_map)
    else:
        heatmap = sns.heatmap(corr_df.sort_values(by=target, ascending=False),
                              vmin=-1, vmax=1, annot=True, cmap=color_map)
    return heatmap.set_title(f'Features Correlating with {target}', fontdict={'fontsize': 18}, pad=16)


def create_feature_importance_charts(models: list, X_train_impute_df: pd.DataFrame()) -> List[alt.Chart]:
    """Given a list of best models, this function charts feature importances if the model has that property

    :param models: List of models that have been hypertuned 
    :param X_train_impute_df: feature dataframe
    :returns: chart_list : list of Altair charts that can be displayed
    """
    chart_list = []
    for best_model in models:
        if hasattr(best_model.best_estimator_, 'feature_importances_'):
            color_for_bars = sjv_blue
            feature_imp_dict = pd.DataFrame(
                {
                    "Feature Number": range(len(best_model.best_estimator_.feature_importances_)),
                    "Feature Name": list(X_train_impute_df.columns),
                    "Feature Importance": best_model.best_estimator_.feature_importances_,
                }
            )
            chart = (
                alt.Chart(feature_imp_dict, title=type(best_model.best_estimator_.regressor_).__name__)
                .mark_bar(color=color_for_bars)
                .encode(x=alt.X("Feature Name:N", sort="-y"), y="Feature Importance:Q")
            )
            chart_list.append(chart)
    return chart_list


def sjv_heat_color(value: float, reverse: bool = False) -> str:
    """This function returns a color for a given value in a range of colors

    :param value: value to be mapped to a color
    :param reverse: Flag True/False indicating if the color mapping should be reversed
    :returns: color : color for the given value
    """
    min_c = np.array([0.3765, 0.5569, 0.7569])
    middle_c = np.array([0.6863, 0.4157, 0.6039])
    max_c = np.array([0.8902, 0.4431, 0.0745])
    if reverse:
        min_c = np.array([0.8902, 0.4431, 0.0745])
        max_c = np.array([0.3765, 0.5569, 0.7569])
    if value <= 0.5:
        color = np.rint((min_c + (middle_c - min_c) * value)*255).astype(int)
    else:
        color = np.rint((middle_c + (max_c - middle_c) * value)*255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])


def sjv_heat_colormap(value: float) -> str:
    """This function is a colormap function. It returns a color for a given value in a range of colors

    :param value: value to be mapped to a color
    :returns: color : color for the given value
    """
    if math.isnan(value) is False:
        y = sjv_heat_color(value)
    else:
        y = sjv_error
    return y


def sjv_heat_colormap_reverse(value: float) -> str:
    """This function is a colormap function. It returns a color for a given value in an inverse range of colors

    :param value: value to be converted to color
    :returns: color in hex format
    """
    if math.isnan(value) is False:
        y = sjv_heat_color(value, reverse=True)
    else:
        y = sjv_error
    return y


def create_correlation_scatters(df: pd.DataFrame, x_feature: str, y_feature: str, x_axis_title: str) -> alt.Chart:
    """This function creates a scatter chart and a line that is a regression line between the two numerical columns
    passed to it. It prints out the correlation values as well

    :param df: Dataframe containing the features to be plotted
    :param x_feature: name of the feature to be plotted on the x-axis
    :param y_feature: name of the target feature to be plotted on the y-axis
    :param x_axis_title: name of the x-axis Title
    """
    corr = df[y_feature].corr(df[x_feature])
    source = df
    base = alt.Chart(source)

    chart = base.mark_circle().encode(
        alt.X(f"{x_feature}:Q", axis=alt.Axis(title=x_axis_title)),
        alt.Y(f"{y_feature}:Q"),
        color="YEAR:N"
    ).properties(
        width=300,
        height=150
    )
    text = base.mark_text(
                            align="left", baseline="top"
                        ).encode(
                        x=alt.value(5),  # pixels from left
                        y=alt.value(5),  # pixels from top
                        text=alt.value(f"corr: {corr:.3f}"),
                        )
    corr_chart = chart + text + chart.transform_regression(x_feature, y_feature).mark_line(
        color='darkblue').encode(color=alt.value('blue'))
    return corr_chart


def chart_feature_target_relation(x_df: pd.DataFrame, y: pd.Series, feature: str, target: str) -> alt.Chart:
    """This function returns the correlation coefficient of each feature with respect to target

    :param x_df: The fetaures DataFrame containing feature = variable
    :param y: Series containing target
    :param: feature: Name of feature to correlate with target 
    :param target: Name of target
    """
    feature_to_target_df_year = x_df.reset_index()
    y_year = pd.DataFrame(y).reset_index()

    # normalize the target
    y_year[target] = np.sqrt(y_year[target])

    total_df = pd.concat([feature_to_target_df_year, y_year[[target]]], axis=1)
    total_chart_df = pd.melt(total_df, id_vars=['TOWNSHIP_RANGE', 'YEAR', target])
    total_chart_df = total_chart_df[total_chart_df['variable'] == feature]
    return create_correlation_scatters(total_chart_df, "value", target, feature)


def get_feature_target_correlation(X_df: pd.DataFrame, y_target: pd.Series, target: str = 'GSE_GWE') -> pd.DataFrame:
    """This function returns the correlation coefficient of each feature with respect to target

    :param X_df: The features DataFrame 
    :param y_target: Series containing target
    :param target: Name of target
    """
    variable_corr_dict = {}
    y_df = pd.DataFrame(y_target)

    # normalize the target
    y_df[target] = np.sqrt(y_df[target])

    full_df = pd.concat([X_df, y_df], axis=1)
    for col in full_df.columns:
        corr = full_df[target].corr(full_df[col])
        variable_corr_dict[col] = corr
    corr_df = pd.DataFrame.from_dict(variable_corr_dict, orient='index', columns=['Correlation_Coefficient'])
    corr_df['sort_coeff'] = np.abs(corr_df['Correlation_Coefficient'])
    corr_df = corr_df.sort_values(['sort_coeff'], ascending=False)
    return corr_df.drop(columns=['sort_coeff'])


def draw_missing_data_chart(df: pd.DataFrame) -> alt.Chart:
    """This function charts the percentage missing data in the data file read in

    :param df: The Pandas DataFrame for which to draw missing data
    """
    percent_missing = df.isnull().sum() / len(df)
    missing_value_df = pd.DataFrame({'column_name': df.columns,
                                     'percent_missing': percent_missing})
    missing_value_df.sort_values('percent_missing', ascending=False, inplace=True)

    sort_list = list(missing_value_df['column_name'])
    chart = alt.Chart(missing_value_df).mark_bar(color=sjv_blue).encode(
        y=alt.Y("sum(percent_missing)", stack="normalize", axis=alt.Axis(format='%')),
        x=alt.X('column_name:N', sort=sort_list),
        color=alt.value(sjv_blue),
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


def get_base_map(gdf: gpd.GeoDataFrame, color: str, opacity: float) -> alt.Chart:
    """This function creates and returns an base map with Altair from the GeoDataFrame

    :param gdf: The geopandas DataFrame from which to generate the Altair base map
    :param color: Color for the area
    :param opacity: Opacity to apply to the color
    """
    base_gdf = gdf.set_crs('epsg:4326')
    # Set the class's base chart
    return alt.Chart(base_gdf).mark_geoshape(
                        stroke='black',
                        strokeWidth=1
                    ).encode(
                        color=alt.value(color),
                        opacity=alt.value(opacity),
                    ).properties(
                        width=500,
                        height=500
                    )


def get_stations_chart(stations_gdf: gpd.GeoDataFrame, tooltip_columns: List[str]) -> alt.Chart:
    """This function creates and returns an Altair chart of the stations

    :param stations_gdf: The GeoDataFrame containing the stations data
    :param tooltip_columns: The columns to display in the tooltip
    """
    if "points" in list(stations_gdf.columns):
        points_df = stations_gdf.copy()
        points_df.drop(columns=["geometry"], inplace=True)
        points_df.set_geometry("points", inplace=True)
        stations_chart = alt.Chart(points_df).mark_geoshape().encode(
            color=alt.value('black'),
            tooltip=tooltip_columns,
        )
    else:
        stations_chart = alt.Chart(stations_gdf).mark_circle().encode(
            latitude='LATITUDE:Q',
            longitude='LONGITUDE:Q',
            tooltip=tooltip_columns,
            fill=alt.value('black'),
        )
    return stations_chart


def view_year_with_slider(base_map, gdf: gpd.GeoDataFrame, color_col: str, color_scheme: str = 'blues',
                          time_col: str = 'YEAR', draw_stations: bool = False) -> alt.Chart:
    """This function generates an interactive visualization of the data with a slider

    :param base_map: The Altair chart to use as the base map
    :param gdf: The GeoDataFrame containing the data
    :param color_col: The column to use for the color
    :param color_scheme: The color scheme to use for the areas
    :param time_col: The column to use for the time
    :param draw_stations: If True, draw the stations
    """
    gdf = gdf.set_crs('epsg:4326')
    # Limit the time range so that the chart can be shown
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


def simple_geodata_viz(gdf: gpd.GeoDataFrame, feature: str, title: str, year: int = None, color_scheme: str = 'blues',
                       draw_stations: bool = False) -> alt.Chart:
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


def view_trs_side_by_side(gdf: gpd.GeoDataFrame, feature: str, value: str, title: str, color_scheme: str = "sjv",
                          reverse_palette: bool = False, draw_stations: bool = False, small_multiple_size: int = 350) \
        -> alt.Chart:
    """ This function creates a side by side Altair visualization of the Township-Ranges for the given feature

    :param gdf: the geodataframe to be visualized
    :param feature: the name of the DataFrame column used for the small multiples facets
    :param value: the name of the DataFrame column containing the Township-Ranges values
    :param title: the title of the visualization
    :param color_scheme: the color scheme to be used
    :param reverse_palette: if True, the color palette will be reversed
    :param draw_stations: if True, the stations will be drawn on each sur chart
    :param small_multiple_size: the size of the small multiples charts
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
        color_range = [sjv_blue, sjv_brown]
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
        if reverse_palette:
            color_scale = alt.Scale(range=reversed(color_range))
        else:
            color_scale = alt.Scale(range=[sjv_blue, sjv_brown])
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
            width=small_multiple_size,
            height=small_multiple_size
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
                width=small_multiple_size,
                height=small_multiple_size,
                title=feature_
            )
            for feature_ in sorted(area_df[feature].unique())
        ),
                           columns=3
                           ).properties(title=title)
    return chart


def visualize_seasonality_by_month(gdf: gpd.GeoDataFrame, feature: List[str]) -> alt.Chart:
    """ This function visualizes the seasonality of the data by month

    :param gdf: the geodataframe to visualize
    :param feature: the feature to visualize
    :return: the Altair visualization
    """
    viz_gdf = gdf.copy()
    viz_gdf["DATE"] = viz_gdf.apply(lambda row: datetime(row.YEAR, row.MONTH, 1), axis=1)
    chart = alt.Chart(viz_gdf[viz_gdf["YEAR"] >= 2000]).mark_bar(color=sjv_blue).encode(
        y=f"{feature}:Q",
        x="DATE:T",
        tooltip=["YEAR", "MONTH", f"{feature}:Q"]
    ).properties(width=800)
    return chart


def display_data_on_map(gdf: gpd.GeoDataFrame, feature: str, year: int = None, categorical: bool = False,
                        color_scheme: str = "sjv", reverse_palette: bool = False):
    """Use GeoPandas explore() function based on Folium to display the Geospatial data on a map.

    :param gdf: the GeoDataFrame to be displayed
    :param feature: the feature to be displayed
    :param year: the year to be displayed
    :param categorical: whether the data are categorical or not
    :param color_scheme: the color palette to be used
    :param reverse_palette: if True, the color palette will be reversed
    :return: the Folium map
    """
    legend = True
    if color_scheme == "sjv":
        nb_categories = len(gdf[feature].unique())
        if categorical and 2 < nb_categories < len(sjv_color_range_17):
            cmap = sjv_color_range_17[0::len(sjv_color_range_17)//(nb_categories-1)]
            cmap[-1] = sjv_brown
            if reverse_palette:
                cmap = reversed(cmap)
        elif categorical and nb_categories == 2:
            cmap = [sjv_blue, sjv_brown]
            if reverse_palette:
                cmap = [sjv_brown, sjv_blue]
        else:
            cmap = sjv_heat_colormap
            if reverse_palette:
                cmap = sjv_heat_colormap_reverse
            # There is an issue in Folium when we use custom palette and legend
            # It seems it only accepts default palettes for the legend
            legend = False
    else:
        cmap = color_scheme
    if year:
        return gdf[gdf.YEAR == year].explore(feature, cmap=cmap, legend=legend)
    else:
        return gdf.explore(feature, cmap=cmap, legend=legend)


def draw_corr_heatmap(df: pd.DataFrame, drop_columns: List[str] = None) -> alt.Chart:
    """Function to generate an Altair heatmap vizualisation for a dataframe
    
    :params df : pd.Dataframe Dataframe with features
    :param drop_columns: Category columns should not be included in the correlation map
    :return: Altair heatmap chart
    """
    sort_cols = ['AVERAGE_YEARLY_PRECIPITATION', 'GROUNDSURFACEELEVATION_AVG', 'PCT_OF_CAPACITY', 'POPULATION_DENSITY',
                 'STATICWATERLEVEL_AVG', 'TOPOFPERFORATEDINTERVAL_AVG', 'TOTALCOMPLETEDDEPTH_AVG',
                 'TOTALDRILLDEPTH_AVG', 'BOTTOMOFPERFORATEDINTERVAL_AVG', 'WELLYIELD_AVG', 'WELL_COUNT_AGRICULTURE',
                 'WELL_COUNT_DOMESTIC', 'WELL_COUNT_INDUSTRIAL', 'WELL_COUNT_PUBLIC', 'CROP_C', 'CROP_C6', 'CROP_D10',
                 'CROP_D12', 'CROP_D13', 'CROP_D14', 'CROP_D15', 'CROP_D16', 'CROP_D3', 'CROP_D5', 'CROP_D6', 'CROP_F1',
                 'CROP_F10', 'CROP_F16', 'CROP_F2', 'CROP_G',  'CROP_G2', 'CROP_G6', 'CROP_I', 'CROP_P1', 'CROP_P3',
                 'CROP_P6', 'CROP_R', 'CROP_R1', 'CROP_T10', 'CROP_T15', 'CROP_T18', 'CROP_T19', 'CROP_T21', 'CROP_T26',
                 'CROP_T30', 'CROP_T31', 'CROP_T4', 'CROP_T6', 'CROP_T8', 'CROP_T9', 'CROP_V', 'CROP_V3', 'CROP_YP',
                 'SOIL_ALFISOLS_B', 'SOIL_ALFISOLS_C', 'SOIL_ALFISOLS_D', ' SOIL_ARIDISOLS_B', 'SOIL_ARIDISOLS_C',
                 'SOIL_ARIDISOLS_D', 'SOIL_ENTISOLS_A', 'SOIL_ENTISOLS_B', 'SOIL_ENTISOLS_C', 'SOIL_ENTISOLS_D',
                 'SOIL_HISTOSOLS_C', 'SOIL_INCEPTISOLS_B', 'SOIL_INCEPTISOLS_D', 'SOIL_MOLLISOLS_B', 'SOIL_MOLLISOLS_C',
                 'SOIL_MOLLISOLS_D', 'SOIL_ROCK_OUTCROP_D', 'SOIL_VERTISOLS_D', 'SOIL_WATER_',
                 'VEGETATION_BLUE_OAK-GRAY_PINE', 'VEGETATION_CALIFORNIA_COAST_LIVE_OAK', 'VEGETATION_CANYON_LIVE_OAK',
                 'VEGETATION_HARD_CHAPARRAL', 'VEGETATION_KNOBCONE_PINE', 'VEGETATION_NON-NATIVE_HARDWOOD_FOREST',
                 'VEGETATION_PINYON-JUNIPER']
    
    alt.data_transformers.disable_max_rows()
    if drop_columns:
        chart_df = df.drop(columns=drop_columns)
    else:
        chart_df = df

    # The stacking results in an index on the correlation values, we need the index as normal columns for Altair
    cor_data = (chart_df.corr().stack()
                .reset_index()
                .rename(columns={0: 'correlation', 'level_0': 'feature_1', 'level_1': 'feature_2'}))
    cor_data['correlation_label'] = cor_data['correlation'].map('{:.2f}'.format)  # Round to 2 decimal
    
    base = alt.Chart(cor_data).encode(
         x=alt.X("feature_1:N", sort=sort_cols),
         y=alt.Y("feature_2:N", sort=sort_cols),
         tooltip=[alt.Tooltip("feature_1:N", title='feature_1'),
                  alt.Tooltip("feature_2:N", title='feature_2'),
                  alt.Tooltip("correlation_label:Q", title='Correlation Value')],
    ).properties(width=alt.Step(10), height=alt.Step(10))

    rects = base.mark_rect().encode(
        color=alt.Color('correlation_label:Q', scale=alt.Scale(scheme="lightgreyteal"))
    ).properties(width=1000, height=1000)
        
    return rects


def draw_components_variance_chart(pca) -> alt.Chart:
    """This function creates a scree plot. A scree plot plots the explained variance against number of components
    and helps determine the number of components to pick.

    params: pca: pca object fit to the data
    returns: Dataframe with NaNs replaced for vegetation and crops columns
    """
    df = pd.DataFrame({
        'n_components': range(1, pca.n_components_ + 1),
        'explained_variance': pca.explained_variance_ratio_
    })
    return alt.Chart(df).mark_line(color=sjv_blue).encode(x='n_components:O', y='explained_variance:Q')


def biplot(score, coeff, maxdim, pcax, pcay, labels=None):
    """ This function uses:
    score - the transformed data returned by pca - data as expressed according to the new axis
    coeff - the loadings from the pca_components_
      
    For the feaures we are interested in, it plots the correlation between the original features and the PCAs.
    Use cosine similarity and angle measures between axes.

    It shows how the data is related to the ORIGINAL features in the positive and negative direction.

    :param: score is the value of data points as per the linear combination of the principal axes
    :param:coeff: are the eigen values of the eigen vectors
    :param:pcax: The horizontal X-axis
    :param:pcay: The vertical y-axis
    :return: A biplot chart
    """
    zoom = 0.5
    pca1 = pcax-1
    pca2 = pcay-1
    xs = score[:, pca1]
    ys = score[:, pca2]
    n = min(coeff.shape[0], maxdim)
    width = 2.0 * zoom
    scalex = width/(xs.max() - xs.min())
    scaley = width/(ys.max() - ys.min())
    text_scale_factor = 1.3
        
    fig = plt.gcf()
    fig.set_size_inches(16, 16)
    
    plt.scatter(xs*scalex, ys*scaley, s=9)
    for i in range(n):
        plt.arrow(0, 0, coeff[i, pca1], coeff[i, pca2],
                  color=sjv_blue, alpha=0.9, head_width=0.03 * zoom)
        if labels is None:
            plt.text(coeff[i, pca1] * text_scale_factor,
                     coeff[i, pca2] * text_scale_factor,
                     "Var"+str(i+1), color=sjv_brown, ha='center', va='center')
        else:
            plt.text(coeff[i, pca1] * text_scale_factor,
                     coeff[i, pca2] * text_scale_factor,
                     labels[i], color=sjv_brown, ha='center', va='center')
    
    plt.xlim(-zoom, zoom)
    plt.ylim(-zoom, zoom)
    plt.xlabel("PC{}".format(pcax))
    plt.ylabel("PC{}".format(pcay))
    plt.grid()
    return plt


def draw_feature_importance(feature_list: list, importance_list: list) -> alt.Chart:
    """This function charts the percentage missing data in the data file read in

    :param feature_list: The list of features for which the regressor provides importance values
    :param importance_list: Values of feature importance
    :return: An Altair bar chart
    """
    df = pd.DataFrame({"Feature Name": feature_list, "Importance": importance_list})
    feature_imp_chart = alt.Chart(df).mark_bar(color=sjv_blue).encode(
        x=alt.X("Feature Name:N", sort="-y"),
        y="Importance:Q"
    )
    return feature_imp_chart


def draw_histogram(df: pd.DataFrame, col_name: str) -> alt.Chart:
    """This function charts the percentage missing data in the data file read in

    :param df: Dataframe in which resides the column for which histogram is to be plotted
    :param col_name: Name of column for which histogram is to be plotted
    """
    x_mean = np.round(df[col_name].mean(), 2)
    x_median = np.round(df[col_name].median(), 2)
    base = alt.Chart(df)

    mean_df = pd.DataFrame({
        'x': [x_mean, x_median],
        'y': [1000, 1100],
        'value': [f"Mean = {x_mean}", f"Median = {x_median}"]})

    txt_chart = alt.Chart(mean_df).mark_text(
        align='left', 
        fontSize=15,
        color="black"
    ).encode(
        y='y:Q',
        text=alt.Text('value:N'),
    )

    hist = base.mark_bar(color=sjv_blue).encode(
                    alt.X(f"{col_name}:Q", bin=True),
                    y='count()',
                )
    return (txt_chart + hist).configure_axis(grid=False)


def draw_two_lines_with_two_axis(df: pd.DataFrame, x: str, y1: str, y2: str,
                                 title: str, x_title: str, y1_title: str, y2_title) -> alt.Chart:
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


def draw_faceted_two_lines_with_two_axis(df: pd.DataFrame, x: str, y1: str, y2: str, facet: str,
                                         title: str, x_title: str, y1_title: str, y2_title, facet_titles: List[str]) \
        -> alt.Chart:
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
    :param facet_titles: the titles of the facets
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


def draw_faceted_lines(df: pd.DataFrame, x: str, y: str, facet: str, title: str, x_title: str, y_title: str) \
        -> alt.Chart:
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
    if 2 < nb_facets < len(sjv_color_range_17):
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


def draw_small_multiples_bar_charts(df: pd.DataFrame, x: str, y: str, facet: str, facet_sort: List[str], title: str) \
        -> alt.Chart:
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


def draw_hierarchical_parameters_results(df: pd.DataFrame, x: str, y: str, facet: str, title: List[str], x_title: str,
                                         y_title: str, nb_facet_columns: int = 2) -> alt.Chart:
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
    if 2 < nb_facets < len(sjv_color_range_17):
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


def create_silhoutte_cluster_viz(X_train_impute: np.ndarray, random_seed: int):
    """This function plots a pair of visualizations for every number of KMeans cluster chosen.
    This code was taken from scikit-learn documentation
    https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html

    :param X_train_impute: the Dataframe with the data to clustered
    :param random_seed: the random seed for the KMeans clustering
    :return: the pyplot visualization
    """
    range_n_clusters = [2, 3, 4, 5, 6]

    for n_clusters in range_n_clusters:
        # Create a subplot with 1 row and 2 columns
        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.set_size_inches(18, 7)

        # The 1st subplot is the silhouette plot
        # The silhouette coefficient can range from -1, 1 but in this example all
        # lie within [-0.3, 1]
        ax1.set_xlim([-0.3, 1])
        # The (n_clusters+1)*10 is for inserting blank space between silhouette
        # plots of individual clusters, to demarcate them clearly.
        ax1.set_ylim([0, len(X_train_impute) + (n_clusters + 1) * 10])

        # Initialize the clusterer with n_clusters value and a random generator
        # seed of 10 for reproducibility.
        clusterer = KMeans(n_clusters=n_clusters, random_state=random_seed)
        cluster_labels = clusterer.fit_predict(X_train_impute)

        # The silhouette_score gives the average value for all the samples.
        # This gives a perspective into the density and separation of the formed
        # clusters
        silhouette_avg = silhouette_score(X_train_impute, cluster_labels)
        print(
            "For n_clusters =",
            n_clusters,
            "The average silhouette_score is :",
            silhouette_avg,
        )

        # Compute the silhouette scores for each sample
        sample_silhouette_values = silhouette_samples(X_train_impute, cluster_labels)

        y_lower = 10
        for i in range(n_clusters):
            # Aggregate the silhouette scores for samples belonging to
            # cluster i, and sort them
            ith_cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]

            ith_cluster_silhouette_values.sort()

            size_cluster_i = ith_cluster_silhouette_values.shape[0]
            y_upper = y_lower + size_cluster_i

            color = cm.tab10(float(i) / n_clusters)
            ax1.fill_betweenx(
                np.arange(y_lower, y_upper),
                0,
                ith_cluster_silhouette_values,
                facecolor=color,
                edgecolor=color,
                alpha=0.7,
            )

            # Label the silhouette plots with their cluster numbers at the middle
            ax1.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))

            # Compute the new y_lower for next plot
            y_lower = y_upper + 10  # 10 for the 0 samples

        ax1.set_title("The silhouette plot for the various clusters.")
        ax1.set_xlabel("The silhouette coefficient values")
        ax1.set_ylabel("Cluster label")

        # The vertical line for average silhouette score of all the values
        ax1.axvline(x=silhouette_avg, color="red", linestyle="--")

        ax1.set_yticks([])  # Clear the yaxis labels / ticks
        ax1.set_xticks([-0.1, 0, 0.2, 0.4, 0.6, 0.8, 1])

        # 2nd Plot showing the actual clusters formed
        colors = cm.tab10(cluster_labels.astype(float) / n_clusters)
        ax2.scatter(
            X_train_impute[:, 0], X_train_impute[:, 1], marker=".", s=30, lw=0, alpha=0.7, c=colors, edgecolor="k"
        )

        # Labeling the clusters
        centers = clusterer.cluster_centers_
        # Draw white circles at cluster centers
        ax2.scatter(
            centers[:, 0],
            centers[:, 1],
            marker="o",
            c="white",
            alpha=1,
            s=200,
            edgecolor="k",
        )

        for i, c in enumerate(centers):
            ax2.scatter(c[0], c[1], marker="$%d$" % i, alpha=1, s=50, edgecolor="k")

        ax2.set_title("The visualization of the clustered data.")
        ax2.set_xlabel("Feature space for the 1st feature")
        ax2.set_ylabel("Feature space for the 2nd feature")

        plt.suptitle(
            "Silhouette analysis for KMeans clustering on sample data with n_clusters = %d"
            % n_clusters,
            fontsize=14,
            fontweight="bold",
        )

    return plt


def chart_error_distribution(error_df: pd.DataFrame):
    """ This function charts the distribution of errors in the given dataframe
    :param : Error dataframe with absolute error and column with model names
    :return: Altair chart
    """
    return (
        alt.Chart(error_df, title="Error distribution by model")
        .mark_bar(color=sjv_color_range_17[3], opacity=0.4)
        .encode(alt.X("absolute_error:Q", bin=True), y="count()", tooltip=["count()"])
        .properties(width=400, height=125)
        .facet(facet="model_name:N", columns=2)
    )


def chart_error_by_depth(error_df: pd.DataFrame, model_name_list: List):
    """ This function charts the distribution of errors in the given dataframe against the 
        actual test target
    :param : error_df: Error dataframe with absolute error and column with model names
    :param : model_name_list: List of model names e.g. SVR_absolute_error
    :return: Altair chart
    """
    return (
        alt.Chart(
            error_df[error_df["model_name"].isin(model_name_list)],
            title="Error distribution by model",
        )
        .mark_line(color=sjv_color_range_17[16], opacity=0.9)
        .encode(
            alt.X("GSE_GWE_SHIFTED:Q"),
            y="absolute_error:Q",
            tooltip=["model_name", "absolute_error", "TOWNSHIP_RANGE"],
        )
        .properties(width=900, height=125)
        .facet(facet="model_name:N", columns=1)
    )


def chart_error_by_township(error_df: pd.DataFrame, model_name_list: List, num_towns: int = 20):
    """ This function charts the distribution of errors in the given dataframe against the townships
        with the most absolute error.
        The chart can be restricted to the models sent in
    :param : error_df: Error dataframe with absolute error and column with model names
    :param : model_name_list: List of model names e.g. SVR_absolute_error
    :param : num_towns: Number of towns to chart the sorted errors for 
    :return: Altair chart
    """
    errors_by_township_df = (
        error_df[error_df["model_name"].isin(model_name_list)]
        .sort_values(["absolute_error"], ascending=False)
        .groupby("model_name")
        .head(num_towns)
    )
    return errors_by_township_df, (
        alt.Chart(
            errors_by_township_df[
                errors_by_township_df["model_name"].isin(model_name_list)
            ]
        )
        .mark_bar(opacity=1)
        .encode(
            x=alt.X("TOWNSHIP_RANGE:N", sort="-y"),
            y=alt.Y("absolute_error:Q"),
            color=alt.Color(
                "model_name:N",
                scale=alt.Scale(
                    domain=model_name_list,
                    range=[
                        sjv_color_range_9[0],
                        sjv_color_range_17[14],
                        sjv_color_range_17[5],
                    ],
                ),
            ),
            tooltip=["model_name", "absolute_error", "TOWNSHIP_RANGE"],
        )
        .properties(width=850, height=150)
    )        


def chart_depth_diff_error(error_df: pd.DataFrame, full_df: pd.DataFrame) -> alt.Chart:
    """ In order to visually examine if there is a point at which the difference in current year's depth and next year's
     depth  difference impacts the absolute error, chart them against each other with this function. The chart can be
     restricted to the models sent in.

    :param : error_df: Error dataframe with absolute error and column with model names
    :param : full_df: Dataframe with column which is the difference between current year depth and target depth
    :return: Altair chart
    """

    plot_df = error_df[['TOWNSHIP_RANGE', 'model_name', 'absolute_error']].merge(
        full_df[['TOWNSHIP_RANGE', 'depth_diff']], how='inner', left_on='TOWNSHIP_RANGE', right_on='TOWNSHIP_RANGE')
    return alt.Chart(plot_df).mark_line(
        color=sjv_color_range_17[0],
        opacity=.8
    ).encode(
        x='depth_diff:Q',
        y='absolute_error',
        tooltip=['depth_diff', 'absolute_error']
    ).properties(
        width=800,
        height=100
    ).facet(
        facet='model_name',
        columns=1
    )


def draw_hyperparameters_distribution(df: pd.DataFrame, hyperparam_list: List[str] = None, max_rmse: int = 160) \
        -> alt.Chart:
    """ This function draws the distribution of the rmse for all trained models and all hyperparameter values

    :param df: Dataframe with the hyperparameters and the rmse
    :param hyperparam_list: List of display order of the hyperparameters columns
    :param max_rmse: Maximum value of the rmse to display on the X axis
    """
    # Transform the dataframe for faceting with Altair
    # All hyperparameters columns are melted into hyperparameter_name and hyperparameter_value columns
    hpt_df = pd.melt(df, id_vars=["rmse"], var_name="hyperparameter_name", value_name="hyperparameter_value")
    # The mean of the RMSE for a specific hyperparameter value is calculated to color the small-multiple chart
    hpt_df["rmse_mean"] = hpt_df.groupby(["hyperparameter_name", "hyperparameter_value"])["rmse"].transform("mean")
    # We created bins of RMSE values of size 10 to smoothen the distribution plot
    max_bins = math.ceil(hpt_df["rmse"].max() / 10) * 10
    hpt_df["rmse_bin"] = list(pd.cut(hpt_df["rmse"], bins=range(0, max_bins, 10), labels=range(0, max_bins-10, 10)))
    hpt_df.reset_index(inplace=True, drop=True)
    hpt_df = hpt_df.groupby(
        ["hyperparameter_name", "hyperparameter_value", "rmse_mean", "rmse_bin"]).size().reset_index()
    hpt_df.rename(columns={0: "count"}, inplace=True)
    # We filter models trained with hyperparameters resulting in too high RMSE to reduce the chart size
    hpt_df = hpt_df[hpt_df["rmse_bin"] <= max_rmse]
    # Parameters used to control the vertical overlap between small multiples
    step = 50
    overlap = 1
    hyperparam_chart = None
    # If not specific display order is passed, take the values from hyperparameter_name as the default
    if not hyperparam_list:
        hyperparam_list = hpt_df["hyperparameter_name"].unique()
    for hyperparameter in hyperparam_list:
        chart_df = hpt_df[hpt_df["hyperparameter_name"] == hyperparameter].reset_index(drop=True)
        # Dinamically compute each chart title padding to align them
        # We do that based on the max hyperparameter_value of the top chart for that column (hyperparameter)
        # And the max hyperparameter_value amongst all charts in that column (hyperparameter)
        top_hp_val = chart_df.loc[0, "hyperparameter_value"]
        top_hp_df = chart_df[chart_df["hyperparameter_value"] == top_hp_val]
        chart_title_y_padding = (1 - top_hp_df["count"].max()/chart_df["count"].max())*70
        # By default the row feature is numerical, except for the Optimizer hyperparameter where it is a string
        row_feature = "hyperparameter_value:Q"
        if hyperparameter == "optimizer":
            row_feature = "hyperparameter_value:N"
        hp_dist = alt.Chart(chart_df, width=250, height=50).mark_area(
            interpolate='monotone',
            fillOpacity=0.8,
            stroke='lightgray',
            strokeWidth=0.5
        ).encode(
            alt.X(
                "rmse_bin:Q",
                title="RMSE",
                axis=alt.Axis(grid=False)),
            alt.Y(
                "count:Q",
                scale=alt.Scale(range=[step, -step * overlap]),
                axis=None),
            alt.Fill(
                "rmse_mean:Q",
                legend=alt.Legend(
                    title=["RMSE mean value for all models", "trained with the hyperparameter value",
                           "(the lower the better)"],
                    titleLimit=300,
                    direction="horizontal",
                    orient="none",
                    gradientLength=300,
                    gradientThickness=30,
                    legendX=50,
                    legendY=400
                ),
                scale=alt.Scale(range=[sjv_blue, sjv_brown])
            )
        ).facet(
            row=alt.Row(
                row_feature,
                title=None,
                header=alt.Header(labelAngle=0, labelAlign="left")
            )
        ).properties(
            title={
                "text": hyperparameter,
                "dy": -20 - chart_title_y_padding
            },
            bounds="flush"
        )
        if hyperparam_chart is None:
            hyperparam_chart = hp_dist
        else:
            hyperparam_chart |= hp_dist
    hyperparam_chart = hyperparam_chart.properties(
        title={
            "text": ["Distribution of the Root Mean Square Error (RMSE) on the validation set, "
                     "for all trained LSTM models depending on the hyperparameter values"],
            "subtitle": ["(The lower the RMSE the better)"],
            "anchor": "start",
            "fontSize": 20,
            "fontWeight": "bold",
            "dy": -30
        },
        padding=30
    ).configure_facet(
        spacing=0
    ).configure_view(
        stroke=None
    )
    return hyperparam_chart
