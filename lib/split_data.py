import numpy as np
import pandas as pd

import random
from itertools import islice

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit, TimeSeriesSplit


def group_split(list_to_split:str, split_ratio:float=0.8, random_seed=42):
    """This function splits a list into two parts as per split ratio
    """

    random.seed(random_seed)
    random.shuffle(list_to_split)
    list_len = len(list_to_split)
    train_len, remainder = divmod(list_len, 1/split_ratio)
    test_len = list_len-train_len
    split_lengths =  [train_len, test_len]

    # Using islice
    output_lists = [list(islice(list(list_to_split), int(elem))) for elem in [train_len, test_len]]

    return output_lists


def train_test_split_single_level_index (df: pd.DataFrame, index_to_split:str='TOWNSHIP_RANGE', split_ratio:float=0.8, random_seed:int=42):
    """This function splits the dataframe into train and test sets based on one index level of a multi-level index.

    :param df: dataframe to be split
    :param index_to_split: index column name to base the split on
    :param split_ratio: the ratio ito which the test and train datasets need to be split
    :param random_seed: random seed to be used for the split
    :return: train and test dataframes
    """

    townshiprange_list = list(df.index.get_level_values(level=index_to_split).unique().sort_values().values)
    train_list, test_list  = group_split(townshiprange_list, split_ratio, random_seed)

    train_df = df.loc[train_list, :].copy()
    test_df = df.loc[test_list, :].copy()
    train_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    test_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    return train_df, test_df


def train_test_group_split(df: pd.DataFrame, index: List[str], group: str, random_seed=42) -> \
        Tuple[pd.DataFrame, pd.DataFrame]:
    """This function splits the dataframe into train and test sets based on the group column
    some group time series will be in the train set and others in the test set.

    :param df: dataframe to be split
    :param index: list of index columns
    :param group: the group column name to be used to split the dataframe
    :param random_seed: random seed to be used for the split
    :return: train and test dataframes
    """
    group_splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=random_seed)
    X_no_index = df.reset_index(drop=False)
    split = group_splitter.split(X_no_index, groups=X_no_index[group])
    train_idx, test_idx = next(split)
    X_train = X_no_index.loc[train_idx].set_index(index, drop=True)
    X_test = X_no_index.loc[test_idx].set_index(index, drop=True)
    return X_train, X_test


def train_test_time_split(df: pd.DataFrame, index: List[str], group: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """This function splits the timeseries dataframe into X and y value based on time. The last time point is used
    as the y value and the rest is used as the X value.

    :param df: dataframe to be split
    :param index: list of index columns
    :param group: the group column name
    :return: train and test dataframes
    """
    Xy = df.copy()
    Xy.reset_index(inplace=True)
    Xy.sort_values(by=["YEAR"], ascending=True, inplace=True, ignore_index=True)
    tr_splitter = TimeSeriesSplit(n_splits=2, test_size=len(Xy[group].unique()))
    split = tr_splitter.split(Xy)
    next(split)
    train_idx, test_idx = next(split)
    X = Xy.loc[train_idx].set_index(index, drop=True)
    X.sort_index(level=index, inplace=True)
    y = Xy.loc[test_idx].set_index(index, drop=True)
    y.sort_index(level=index, inplace=True)
    return X, y


def train_test_group_time_split(df: pd.DataFrame, index: List[str], group: str, random_seed=42) -> \
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """This function splits the timeseries dataframe into train and test sets and X and y data based on the group column
     and time. Based on the group column, some group time series will be in the train set and others in the test set
     The last time point is used as the y value and the rest is used as the X value.

    :param df: dataframe to be split
    :param index: list of index columns
    :param group: the group column name to be used to split the dataframe
    :param random_seed: random seed to be used for the split
    :return: X_train, X_test, y_train, y_test dataframes
    """
    Xy_train, Xy_test = train_test_group_split(df, index=index, group=group, random_seed=random_seed)
    X_train, y_train = train_test_time_split(Xy_train, index=index, group=group)
    X_test, y_test = train_test_time_split(Xy_test, index=index, group=group)
    return X_train, X_test, y_train, y_test
