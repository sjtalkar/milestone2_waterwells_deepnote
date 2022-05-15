import numpy as np
import pandas as pd

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit, TimeSeriesSplit


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
