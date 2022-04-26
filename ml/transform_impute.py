import sys
sys.path.append('..')

import os
import numpy as np
import pandas as pd

from sklearn import set_config
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.utils.validation import check_is_fitted
from sklearn.base import BaseEstimator, TransformerMixin


# The functions in this file are applied on the dataframe to clean and impute missing values


# Functions  for transformations
def convert_scaled_array_to_df(
    X_impute_scaled: np.ndarray,
    cols_transformer: ColumnTransformer,
    X: pd.DataFrame,
    list_cols_used: list,
    drop_cols: list,
):
    """
    This function creates a list of column names to apply to the dataframe created from the numpy array
    output of a column transformer

    Parameters
    ----------
    X_impute_scaled : Array that is returned after imputation and scaling
    cols_transformer: ColumnTransformer
        The column transformer that generated the X_new array
    X     : pd.Dataframe
        Original datafram before transformation containing original column names
    list_cols_used: list
          A list of all the columns that were passed to the column transformer
    drop_cols: list
          Columns that were used for grouping but were dropped from the result of the transformation to avoid duplication

    Returns
    -------
    result : Dataframe with NaNs replaced for vegetation and crops columns
    """

    new_col_names = get_column_names_after_transform(
        cols_transformer,
        X,
        list_cols_used,
        drop_cols,
    )
    last_cols = ["TOWNSHIP_RANGE", "YEAR"]
    scaled_list = [col for col in new_col_names if col not in last_cols]
    df_col_list = scaled_list + last_cols
    X_scaled_df = pd.DataFrame(X_impute_scaled, columns=df_col_list)
    # rearrange the column within dataframe
    X_scaled_df = X_scaled_df[last_cols + scaled_list]

    # Make sure the scaled columns are set as numeric
    X_scaled_df[scaled_list] = X_scaled_df[scaled_list].apply(pd.to_numeric)

    return X_scaled_df


def get_column_names_after_transform(
    cols_transformer: ColumnTransformer,
    X: pd.DataFrame,
    list_cols_used: list,
    drop_cols: list,
):
    """
    This function creates a list of column names to apply to the dataframe created from the numpy array
    output of a column transformer

    Parameters
    ----------
    cols_transformer: ColumnTransformer
        The column transformer that generated the X_new array
    X     : pd.Dataframe
        Original datafram before transformation containing original column names
    list_cols_used: list
          A list of all the columns that were passed to the column transformer
    drop_cols: list
          Columns that were used for grouping but were dropped from the result of the transformation to avoid duplication

    Returns
    -------
    result : Dataframe with NaNs replaced for vegetation and crops columns
    """
    new_col_names = []
    for i in range(len(cols_transformer.transformers)):
        new_col_names += [
            cols_transformer.transformers[i][0] + "_" + s
            for s in cols_transformer.transformers[i][2]
        ]
    # First remove the cols we do not have in the dataframe
    [new_col_names.remove(col) for col in drop_cols if col in new_col_names]

    # Then update the column names
    new_col_names = [
        col.split("_", 1)[1] if ("TOWNSHIP_RANGE" in col) or ("YEAR" in col) else col
        for col in new_col_names
    ]

    # The non-transformed columns will be appended on the right of
    # the array and do not show up in the 'transformers_' method.
    # Add the passthrough columns to the col_names manually
    passthrough_cols = [col for col in X.columns if col not in list_cols_used]
    new_col_names += passthrough_cols
    return new_col_names


def convert_back_df(
    X_new: np.ndarray,
    cols_transformer: ColumnTransformer,
    X: pd.DataFrame,
    list_cols_used: list,
    drop_cols: list,
):

    """
    This function creates a list of column names to apply to the dataframe created from the numpy array
    output of a column transformer

    Parameters
    ----------
    X_new : np.ndarray
        Array containing column transformation output of previous step in pipe that needs to be converted
        to Dataframe
    cols_transformer: ColumnTransformer
        The column transformer that generated the X_new array
    X     : pd.Dataframe
        Original datafram before transformation containing original column names
    list_cols_used: list
          A list of all the columns that were passed to the column transformer
    drop_cols: list
          Columns that were used for grouping but were dropped from the result of the transformation to avoid duplication

    Returns
    -------
    result : Dataframe with NaNs replaced for vegetation columns
    """

    new_col_names = get_column_names_after_transform(
        cols_transformer, X, list_cols_used, drop_cols
    )

    X_new_df = pd.DataFrame(X_new, columns=new_col_names)

    cat_cols = ["TOWNSHIP_RANGE", "YEAR"]
    num_cols = [col for col in X_new_df.columns if col not in cat_cols]

    X_new_df[num_cols] = X_new_df[num_cols].apply(pd.to_numeric)

    return X_new_df


def fill_from_prev_year(df: pd.DataFrame, cols_to_impute: list):
    """
    This function fills the vegetation and crops columns with the values from the year 2014

    Parameters
    ----------
    df             : Dataframe with columns to impute
    cols_to_impute:  list
                     column names in a list of columns that need to be imputed from the year provided
    year_with_data : int
        Year containing data to borrow for rest of the years. This is used only for POPULATION_DENSITY and
        ignored for all other columns.

    Returns
    -------
    result : Dataframe with NaNs replaced for columns in the cols_to_impute list
    """

    # create a copy of the dataframe
    result = df.copy()

    numeric_cols = [
        col
        for col in cols_to_impute
        if ("TOWNSHIP_RANGE" not in col) and ("YEAR" not in col)
    ]

    # Separate out the Crops, Vegetation and Soils columns since they have a very specific set of column to borrow from
    # and conditional columns to fill into

    veg_soil_cols = [col for col in df.columns if "VEGETATION" in col or "SOIL" in col]

    crops_cols = [
        col for col in numeric_cols if "CROP_" in col and col not in veg_soil_cols
    ]
    population_cols = ["POPULATION_DENSITY"]
    # Crops and population are filled from the previous year's value and hence they are trated in a similar fashion
    # Vegetation and Soil on the other hand have a specific year that the vaule is non-null which has to be
    # used to fill the rest of the years.

    subset_df = result[["TOWNSHIP_RANGE", "YEAR"] + veg_soil_cols].copy()
    mean_df = subset_df.groupby(["TOWNSHIP_RANGE"])[veg_soil_cols].mean().reset_index()
    year_df = pd.DataFrame({"YEAR": subset_df["YEAR"].unique()})

    mean_df["key"] = 0
    year_df["key"] = 0

    mean_df = mean_df.merge(year_df, on="key", how="outer")
    mean_df.drop(columns=["key"], inplace=True)

    result.drop(columns=veg_soil_cols, inplace=True)
    result = result.merge(mean_df, how="inner", on=["TOWNSHIP_RANGE", "YEAR"])

    # The crops values can be forward filled once the years are sorted
    crops_ffill_df = result[["YEAR", "TOWNSHIP_RANGE"] + crops_cols].copy()
    crops_ffill_df.sort_values(by=["YEAR", "TOWNSHIP_RANGE"], inplace=True)
    crops_ffill_df = (
        crops_ffill_df.groupby(["TOWNSHIP_RANGE", "YEAR"])[crops_cols]
        .mean()
        .ffill()
        .reset_index()
    )

    # Drop the original column and get all filled values from the new dataframe
    result.drop(columns=crops_cols, inplace=True)
    result = result.merge(crops_ffill_df, how="inner", on=["TOWNSHIP_RANGE", "YEAR"])

    # For population, we capture the trend over the past years 2019 to 2020 and add that to 2020 value
    # This gives us the imputed 2021 value
    all_years = list(result["YEAR"].unique())
    all_years_trend = [f"{year}_trend" for year in all_years]
    pop_df = result[result["YEAR"].isin(all_years)][
        ["TOWNSHIP_RANGE", "YEAR", "POPULATION_DENSITY"]
    ]
    # Pivot the dataframe so that the TOWNSHIP_RANGE forms the index and years are along the columns
    pop_pivot_df = pop_df.pivot(
        index=["TOWNSHIP_RANGE"], columns=["YEAR"], values=["POPULATION_DENSITY"]
    )

    # On the pivot above, find difference between columns to get trend
    diff_df = pop_pivot_df.diff(axis="columns").reset_index()
    diff_df.droplevel(level=0, axis=1)
    diff_df.columns = ["TOWNSHIP_RANGE"] + all_years_trend
    pop_pivot_df = pop_pivot_df.droplevel(level=0, axis=1)
    pop_pivot_df = pop_pivot_df.merge(
        diff_df, how="inner", on=["TOWNSHIP_RANGE"]
    ).reset_index()
    # Add the trend to past year value for 2021
    pop_pivot_df["2021"] = pop_pivot_df["2020"] + pop_pivot_df["2020_trend"]

    pop_pivot_df = pop_pivot_df[["TOWNSHIP_RANGE"] + list(all_years)]
    pop_pivot_df = pd.melt(
        pop_pivot_df,
        id_vars=["TOWNSHIP_RANGE"],
        var_name="YEAR",
        value_name="POPULATION_DENSITY",
    )

    # Get all the POPULATION_DENSITY values from the POPULATION_DENSITY column of new dataframe
    result.drop(columns=population_cols, inplace=True)
    result = result.merge(pop_pivot_df, how="inner", on=["TOWNSHIP_RANGE", "YEAR"])

    return result


class PandasSimpleImputer(SimpleImputer):
    """A wrapper around `SimpleImputer` to return data frames with columns."""

    def fit(self, X, y=None):
        self.columns = X.columns
        return super().fit(X, y)

    def transform(self, X):
        return pd.DataFrame(super().transform(X), columns=self.columns)


# This class uses the base classes from scikit-learn and implements fit-transform
class GroupImputer(BaseEstimator, TransformerMixin):
    """
    Class used for imputing missing values in a pd.DataFrame using either mean or median of a group.

    Parameters
    ----------
    group_by_cols : list
        List of columns used for calculating the aggregated value
    impute_for_col : str
        The name of the column to impute
    aggregation_func : str
        The aggregation function to be used to calculate value to replace nulls with,
        can be one of ['mean', 'median', 'min', 'max']
    Returns
    -------
    df_col : array-like
        The array with imputed values in the impute_for_col column
    """

    def __init__(
        self, group_by_cols: list, impute_for_col: str, aggregation_func="mean"
    ):

        self.group_by_cols = group_by_cols
        self.impute_for_col = impute_for_col
        self.aggregation_func = aggregation_func

    def fit(self, X, y=None):
        # y parameter is present to maintain compatibility with other scikit-learn packages

        impute_for_col = self.impute_for_col
        impute_group_map = (
            X.groupby(self.group_by_cols)[self.impute_for_col]
            .agg(self.aggregation_func)
            .reset_index(drop=False)
        )

        ## In the case of GROUNDSURFACELEVATION_AVG, there can be township ranges where
        ## wells construction reports have never been filed, When the map has empty values, fill it
        ## with the "aggregation_func" value of the entire map TBD!!!
        if self.aggregation_func == "mean":
            impute_group_map[impute_for_col].fillna(
                impute_group_map[impute_for_col].mean(), inplace=True
            )
        elif self.aggregation_func == "median":
            impute_group_map[impute_for_col].fillna(
                impute_group_map[impute_for_col].median(), inplace=True
            )
        elif self.aggregation_func == "min":
            impute_group_map[impute_for_col].fillna(
                impute_group_map[impute_for_col].min(), inplace=True
            )
        elif self.aggregation_func == "max":
            impute_group_map[impute_for_col].fillna(
                impute_group_map[impute_for_col].max(), inplace=True
            )

        self.impute_group_map_ = impute_group_map
        self.columns = X.columns

        # fit method should always return self!!
        return self

    def transform(self, X, y=None):

        # make sure that the imputer was fitted
        check_is_fitted(self, "impute_group_map_")

        # Do not modify the original source data.
        X = X.copy()

        for index, row in self.impute_group_map_.iterrows():
            ind = (X[self.group_by_cols] == row[self.group_by_cols]).all(axis=1)
            X.loc[ind, self.impute_for_col] = X.loc[ind, self.impute_for_col].fillna(
                row[self.impute_for_col]
            )

        # return df.values-----use this if you want to be consistent and return an ndarray

        # Remove the TOWNSHIP_RANGE grouping column
        return_df = pd.DataFrame(X, columns=self.columns)
        # replace TOWNSHIP_RANGE by self.group_by_cols
        return_df.drop(columns=["TOWNSHIP_RANGE"], inplace=True)
        return return_df
