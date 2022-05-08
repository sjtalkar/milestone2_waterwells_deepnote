import os
import pandas as pd
from typing import List, Tuple


# Pick out the csv files that form inidividual features from the assets folder
def read_feature_files(folder_name: str = "../assets/outputs/"):
    """This function loads the feature datasets from the output folder 
       in the local file system.

        :param folder_name: folder path to the measurements dataset.
        :output: a dictionary with dataframe names as key and 
                 the dataframe as value
    """
    output_files_dict = dict()
    for output_file in os.listdir("../assets/outputs/"):
        if output_file != "california_weekly_drought_index.csv":
            output_files_dict[f"{output_file.replace(r'.csv', '')}_df"] = pd.read_csv(rf"{folder_name}{output_file}") 
    return output_files_dict

def read_and_join_output_file(start_year: int = 2014, end_year: int = 2021) -> \
        Tuple[pd.DataFrame, pd.DataFrame]:
    """This function loads the feature datasets from the output folder
       in the local file system and joins them.

    :param start_year: start year for the feature and target dataframes
    :param end_year: last year for the feature and target dataframes
    :return X: The dataframe containing the feature data
    :return y: The dataframe containing the target data
    """
    feature_df_dict = read_feature_files()
    left_df = pd.DataFrame()
    for each_df_name in feature_df_dict.keys():
        # We are considering the year range from 2014 to 2021 for ML
        if left_df.empty:
            # Make the first dataframe the left dataframe, it will be replaced by result of join
            left_df = feature_df_dict[each_df_name]
            left_df = left_df[(left_df['YEAR'] >= start_year) & (left_df['YEAR'] <= end_year)].copy()
            continue

        # Make consecutively arriving dataframes the right dataframe
        right_df = feature_df_dict[each_df_name]
        right_df = right_df[(right_df['YEAR'] >= start_year) & (right_df['YEAR'] <= end_year)].copy()

        join_cols = ['TOWNSHIP_RANGE', 'YEAR']
        join_type = 'outer'
        indicator = False

        left_df = left_df.merge(right_df,
                                on=join_cols,
                                how=join_type,
                                indicator=indicator)

    # Set the TOWNSHIP_RANGE and YEAR as index
    left_df['YEAR'] = left_df['YEAR'].astype(int).astype('str')
    left_df.set_index(['TOWNSHIP_RANGE', 'YEAR'], drop=True, inplace=True)
    left_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    return left_df
    
# def read_and_join_output_file(targets: List[str], start_year: int = 2014, end_year: int = 2021) -> \
#         Tuple[pd.DataFrame, pd.DataFrame]:
#     """This function loads the feature datasets from the output folder
#        in the local file system and joins them.
#
#     :param targets: list of of the target variable in the dataset
#     :param start_year: start year for the feature and target dataframes
#     :param end_year: last year for the feature and target dataframes
#     :return X: The dataframe containing the feature data
#     :return y: The dataframe containing the target data
#     """
#     feature_df_dict = read_feature_files()
#     left_df = pd.DataFrame()
#     for each_df_name in feature_df_dict.keys():
#         # We are considering the year range from 2014 to 2021 for ML
#         if left_df.empty:
#             # Make the first dataframe the left dataframe, it will be replaced by result of join
#             left_df = feature_df_dict[each_df_name]
#             left_df = left_df[(left_df['YEAR'] >= start_year) & (left_df['YEAR'] <= end_year)].copy()
#             continue
#
#         # Make consecutively arriving dataframes the right dataframe
#         right_df = feature_df_dict[each_df_name]
#         right_df = right_df[(right_df['YEAR'] >= start_year) & (right_df['YEAR'] <= end_year)].copy()
#
#         join_cols = ['TOWNSHIP_RANGE', 'YEAR']
#         join_type = 'outer'
#         indicator = False
#
#         left_df = left_df.merge(right_df,
#                                 on=join_cols,
#                                 how=join_type,
#                                 indicator=indicator)
#
#     # Set the TOWNSHIP_RANGE and YEAR as index
#     left_df['YEAR'] = left_df['YEAR'].astype(int).astype('str')
#     left_df.set_index(['TOWNSHIP_RANGE', 'YEAR'], drop=True, inplace=True)
#     left_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
#     feature_columns = list(left_df.columns)
#     feature_columns = list(set(feature_columns) - set(targets))
#     X = left_df[feature_columns]
#     y = left_df[targets]
#     return X, y


