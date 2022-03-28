import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

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