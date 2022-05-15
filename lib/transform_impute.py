import numpy as np
import pandas as pd

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit, TimeSeriesSplit


def fill_from_prev_year(df: pd.DataFrame):
    """This function fills the vegetation, crops and soils columns with the values from the previous existing years. E.g. It fills 2015 data from 2014 and 2017 data from 2016.

    :param df: dataframe to be imputed
    :return: imputed dataframe with NaNs values estimated from previous year values
    """
    # Separate out the Crops, Vegetation and Soils columns since they have a very specific set of column to borrow from
    # and conditional columns to fill into
    veg_soil_cols = [col for col in df.columns if col.startswith("VEGETATION_") or col.startswith("SOIL_")]
    crops_cols = [col for col in df.columns if col.startswith("CROP_") and col not in veg_soil_cols]

    # Crops is filled from the previous year's value
    # Vegetation and Soil on the other hand have a specific year that the value is non-null which has to be
    # used to fill the rest of the years.
    subset_df = df[veg_soil_cols].copy()
    value_df = subset_df.groupby(["TOWNSHIP_RANGE"])[veg_soil_cols].mean().reset_index()
    year_df = pd.DataFrame({"YEAR": subset_df.index.unique(level="YEAR")})

    value_df["key"] = 0
    year_df["key"] = 0

    value_df = value_df.merge(year_df, on="key", how="outer")
    value_df.drop(columns=["key"], inplace=True)
    value_df.set_index(['TOWNSHIP_RANGE', 'YEAR'], drop=True, inplace=True)

    # The crops values can be forward filled (the years are already sorted)
    crops_ffill_df = df[crops_cols].copy()
    crops_ffill_df.ffill(inplace=True)

    result = pd.merge(value_df, crops_ffill_df, how="inner", left_index=True, right_index=True)
    # Just make sure that rows are sorted in the original order
    result.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    return result


def estimate_pop_from_prev_year(df: pd.DataFrame):
    """ This function estimates teh population based on the previous year's value and trend

    :param df: dataframe to be imputed
    :return: imputed dataframe with NaNs values estimated from previous year values
    """
    # For population, we capture the trend over the past years 2019 to 2020 and add that to 2020 value
    # This gives us the imputed 2021 value
    all_years = list(df.index.unique(level="YEAR"))
    all_years_trend = [f"{year}_trend" for year in all_years]
    # Pivot the dataframe so that the TOWNSHIP_RANGE forms the index and years are along the columns
    pop_pivot_df = df["POPULATION_DENSITY"].reset_index().pivot(
        index=["TOWNSHIP_RANGE"], columns=["YEAR"], values=["POPULATION_DENSITY"]
    )

    # On the pivot above, find difference between columns to get trend
    diff_df = pop_pivot_df.diff(axis="columns").reset_index()
    diff_df.droplevel(level=0, axis=1)
    diff_df.columns = ["TOWNSHIP_RANGE"] + all_years_trend
    pop_pivot_df = pop_pivot_df.droplevel(level=0, axis=1)
    pop_pivot_df = pop_pivot_df.merge(diff_df, how="inner", on=["TOWNSHIP_RANGE"]).reset_index(drop=True)
    # Add the trend to past year value for 2021
    pop_pivot_df["2021"] = pop_pivot_df["2020"] + pop_pivot_df["2020_trend"]

    pop_pivot_df = pop_pivot_df[["TOWNSHIP_RANGE"] + list(all_years)]
    pop_pivot_df = pd.melt(
        pop_pivot_df,
        id_vars=["TOWNSHIP_RANGE"],
        var_name="YEAR",
        value_name="POPULATION_DENSITY",
    )
    pop_pivot_df.set_index(["TOWNSHIP_RANGE", "YEAR"], inplace=True, drop=True)
    # Just make sure that rows are sorted in the original order
    pop_pivot_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    return pop_pivot_df


class PandasSimpleImputer(SimpleImputer):
    """A wrapper around `SimpleImputer` to return data frames with columns."""

    def fit(self, X, y=None):
        """This function fits the group imputer on the data. In this case, it does nothing.

        :param X: The dataframe to fit on
        :param y: The target values. The y parameter is present to maintain compatibility with other scikit-learn
        packages
        :return: the parent class fit method
        """
        self.columns = X.columns
        return super().fit(X, y)

    def transform(self, X, y=None):
        """This function imputes the missing values in the dataframe.

        :param X: The dataframe to impute on
        :param y: The target values. The y parameter is present to maintain compatibility with other scikit-learn
        :return: The imputed dataframe
        """
        return pd.DataFrame(super().transform(X), columns=self.columns)


# This class uses the base classes from scikit-learn and implements fit-transform
class GroupImputer(BaseEstimator, TransformerMixin):
    """Class used for imputing missing values in a pd.DataFrame using either mean or median of a group.

    :param group_by_cols: List of columns used for calculating the aggregated value
    :param impute_for_col: The column to impute
    :param aggregation_func: The aggregation function to use
    """

    def __init__(self, group_by_cols: List[str], impute_for_col: str, aggregation_func="mean"):
        self.group_by_cols = group_by_cols
        self.impute_for_col = impute_for_col
        self.aggregation_func = aggregation_func

    def fit(self, X, y=None):
        """This function fits the group imputer on the data. In this case, it does nothing.

        :param X: The dataframe to fit on
        :param y: The target values. The y parameter is present to maintain compatibility with other scikit-learn
        packages
        :return: self
        """
        self.columns = X.columns
        # fit method should always return self!!
        return self

    def transform(self, X, y=None):
        """This function imputes the missing values in the dataframe.

        :param X: The dataframe to impute on
        :param y: The target values. The y parameter is present to maintain compatibility with other scikit-learn
        :return: The imputed dataframe
        """
        impute_group_map = X.groupby(self.group_by_cols)[[self.impute_for_col]].agg(self.aggregation_func)

        ## In the case of GROUNDSURFACELEVATION_AVG, there can be township ranges where
        ## wells construction reports have never been filed, When the map has empty values, fill it
        ## with the "aggregation_func" value of the entire map TBD!!!
        if self.aggregation_func == "mean":
            impute_group_map[self.impute_for_col].fillna(
                impute_group_map[self.impute_for_col].mean(), inplace=True
            )
        elif self.aggregation_func == "median":
            impute_group_map[self.impute_for_col].fillna(
                impute_group_map[self.impute_for_col].median(), inplace=True
            )
        elif self.aggregation_func == "min":
            impute_group_map[self.impute_for_col].fillna(
                impute_group_map[self.impute_for_col].min(), inplace=True
            )
        elif self.aggregation_func == "max":
            impute_group_map[self.impute_for_col].fillna(
                impute_group_map[self.impute_for_col].max(), inplace=True
            )
        # Do not modify the original source data.
        return_df = X.copy()
        for index, row in impute_group_map.iterrows():
            return_df.loc[index, self.impute_for_col].fillna(row.values[0], inplace=True)
        return return_df

