import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin


# The functions in this file are applied on the dataframe to clean and impute missing values

# Functions  for transformations
def convert_scaled_array_to_df(
    X_impute_scaled: np.ndarray,
    cols_transformer: ColumnTransformer,
    X: pd.DataFrame,
    list_cols_used: list
    
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
    
    Returns
    -------
    result : Dataframe with NaNs replaced for vegetation and crops columns
    """

    new_col_names = get_column_names_after_transform(
        cols_transformer,
        X,
        list_cols_used
    )
    

    X_scaled_df = pd.DataFrame(X_impute_scaled, index = X.index, columns=new_col_names)
   
    # Make sure the scaled columns are set as numeric
    X_scaled_df[new_col_names] = X_scaled_df[new_col_names].apply(pd.to_numeric)

    return X_scaled_df


def get_column_names_after_transform(
    cols_transformer: ColumnTransformer,
    X: pd.DataFrame,
    list_cols_used: list  
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
  
    Returns
    -------
    result : Dataframe with NaNs replaced for vegetation columns
    """
    orig_cols = X.columns
    new_col_names = []
    for i in range(len(cols_transformer.transformers)):
        new_col_names += [
             s for s in cols_transformer.transformers[i][2]
        ]

    passthrough_cols = [col for col in X.columns if col not in new_col_names]
    new_col_names += passthrough_cols
    return pd.DataFrame(X_new, index = X.index, columns=new_col_names)


def fill_from_prev_year(df: pd.DataFrame):
    """This function fills the vegetation, crops and soils columns with the values from the previous existing years.
    E.g. It fills 2015 data from 2014 and 2017 data from 2016.

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

  
def fill_pop_from_prev_year(df: pd.DataFrame):
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

    # On the pivoted Dataframe , find difference between columns to get trend
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
        List of columns used for calculating the aggregated value. We will be grouping by TOWNSHIP_RANGE alone
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
        self, group_by_cols: list, impute_for_col: str, aggregation_func="median"
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
        )

        ## In the case of GROUNDSURFACELEVATION_AVG, there can be township ranges where
        ## wells construction reports have never been filed, When the map has empty values, fill it
        ## with the "aggregation_func" value of the entire map TBD!!!
        if self.aggregation_func == "mean":
            impute_group_map.fillna(
                impute_group_map.mean(), inplace=True
            )
        elif self.aggregation_func == "median":
            impute_group_map.fillna(
                impute_group_map.median(), inplace=True
            )
        elif self.aggregation_func == "min":
            impute_group_map.fillna(
                impute_group_map.min(), inplace=True
            )
        elif self.aggregation_func == "max":
            impute_group_map.fillna(
                impute_group_map.max(), inplace=True
            )

        self.impute_group_map_ = impute_group_map
        self.columns = X.columns

        # fit method should always return self!!
        return self

    def transform(self, X, y=None):

        # make sure that the imputer was fitted
        #check_is_fitted(self, "impute_group_map_")

        # Do not modify the original source data.
        X_new = X.reset_index().copy()

        # for index, value in self.impute_group_map_.iteritems():
        #     X.loc[index, self.impute_for_col].fillna(value, inplace=True)
        impute_group_map = self.impute_group_map_.reset_index()
         
        for index, row in impute_group_map.iterrows():
            ind = (X_new[self.group_by_cols] == row[self.group_by_cols]).all(axis=1)
            X_new.loc[ind, self.impute_for_col] = X_new.loc[ind, self.impute_for_col].fillna(
                row[self.impute_for_col]
            )
        X_new = X_new.set_index(['TOWNSHIP_RANGE', 'YEAR'], drop=True)
        X_new.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
        return X_new
