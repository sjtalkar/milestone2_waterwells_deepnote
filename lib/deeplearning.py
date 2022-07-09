import numpy as np
import pandas as pd

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from tensorflow import keras


def fill_veg_from_prev_year(df: pd.DataFrame):
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


def create_transformation_cols(X: pd.DataFrame) -> dict:
    """This function creates a list of columns that will undergo column transformation

    :param X: dataframe to be  transformed
    :return: a dictionary of the list of columns per transformer on which ColumnTransformation is to be applied
    """
    # Set column lists for each transformer to work on

    veg_cols = [col for col in X.columns if col.startswith("VEGETATION_")]
    soil_cols = [col for col in X.columns if col.startswith("SOIL_")]
    crops_cols = [col for col in X.columns if col.startswith("CROP_")]
    veg_soils_crops_cols = veg_cols + soil_cols + crops_cols
    population_cols = ["POPULATION_DENSITY"]
    wcr_cols = [
        "TOTALDRILLDEPTH_AVG",
        "WELLYIELD_AVG",
        "STATICWATERLEVEL_AVG",
        "TOPOFPERFORATEDINTERVAL_AVG",
        "BOTTOMOFPERFORATEDINTERVAL_AVG",
        "TOTALCOMPLETEDDEPTH_AVG",
    ]
    pct_cols = ["PCT_OF_CAPACITY"]
    gse_cols = ["GROUNDSURFACEELEVATION_AVG"]
    other_cols = list(set(X.columns) - set(wcr_cols + veg_soils_crops_cols + population_cols + pct_cols + gse_cols) -
                      {"SHORTAGE_COUNT", "GSE_GWE"})

    # Set the columns that go through the ColumnTransformation pipeline
    # list_cols_used = wcr_cols + veg_soils_crops_cols + population_cols + pct_cols + gse_cols + other_cols
    list_cols_used = wcr_cols + veg_soils_crops_cols + population_cols + pct_cols + gse_cols
    columns_to_transform = {
        "wcr": wcr_cols,
        "veg_soils_crops": veg_soils_crops_cols,
        "pop": population_cols,
        "pct": pct_cols,
        "gse": gse_cols,
        "other": other_cols,
        "used": list_cols_used
    }
    return columns_to_transform


def create_transformation_pipelines(X: pd.DataFrame) -> Tuple[Pipeline, List[str]]:
    """This function creates pipelines that will be applied on the train and test datasets

    :param X: dataframe to be  transformed
    :return: a tuple of the pipelines that imputes missing values and he ordered list of column names of the numpy
    array after transformation
    """
    columns_to_transform = create_transformation_cols(X)
    # Transformations through transformers
    wcr_simple_trans = Pipeline(steps=[
        ("imputer", PandasSimpleImputer(missing_values=np.nan, strategy="constant", fill_value=0)),
        ("scaler", MinMaxScaler())
    ])
    # vegetation column transformer
    veg_soil_crops_trans = Pipeline(steps=[
        ("imputer", FunctionTransformer(fill_veg_from_prev_year))
    ])
    pop_trans = Pipeline(steps=[
        ("imputer", FunctionTransformer(estimate_pop_from_prev_year)),
        ("scaler", MinMaxScaler())
    ])

    # pct_of_capacity of a resevoir is set as minimum of future years data per township range
    pct_trans = Pipeline(steps=[
        ("imputer", GroupImputer(group_by_cols=["TOWNSHIP_RANGE"], impute_for_col="PCT_OF_CAPACITY",
                                 aggregation_func="min")),
        ("scaler", MinMaxScaler())])

    # groundsurfaceelevation is set as mean of TownshipRange data per township range
    gse_trans = Pipeline(steps=[
        ("imputer", GroupImputer(group_by_cols=["TOWNSHIP_RANGE"], impute_for_col="GROUNDSURFACEELEVATION_AVG",
                                 aggregation_func="median")),
        ("scaler", MinMaxScaler())])

    cols_transformer = ColumnTransformer(
        transformers=[
            ("wcr", wcr_simple_trans, columns_to_transform["wcr"]),
            ("veg", veg_soil_crops_trans, columns_to_transform["veg_soils_crops"]),
            ("pop", pop_trans, columns_to_transform["pop"]),
            ("pct_capacity", pct_trans, columns_to_transform["pct"]),
            ("gse", gse_trans, columns_to_transform["gse"]),
            #            ("scaler", MinMaxScaler(), columns_to_transform["other"])
        ],
        remainder=MinMaxScaler(),
    )

    remainder_cols = [col for col in X.columns if col not in columns_to_transform["used"]]
    columns = columns_to_transform["used"] + remainder_cols
    impute_pipeline = make_pipeline(cols_transformer)
    return impute_pipeline, columns


def evaluate_forecast(y_test_inverse: np.ndarray, yhat_inverse: np.ndarray) -> Tuple[float, float, float]:
    """This function evaluates the forecasted values against the actual values and returns the following metrics:
    mean absolute error, mean squared error, root mean squared error

    :param y_test_inverse: actual values
    :param yhat_inverse: forecasted values
    :return: a tuple of the mean absolute error, mean squared error, root mean squared error
    """
    mse_ = keras.metrics.MeanSquaredError()
    mae_ = keras.metrics.MeanAbsoluteError()
    rmse_ = keras.metrics.RootMeanSquaredError()
    mae = mae_(y_test_inverse,yhat_inverse)
    print('mae:', mae)
    mse = mse_(y_test_inverse,yhat_inverse)
    print('mse:', mse)
    rmse = rmse_(y_test_inverse,yhat_inverse)
    print('rmse:', rmse)
    return mae, mse, rmse

def reshape_data_to_3d(datasets: List[pd.DataFrame]) -> Tuple[np.ndarray, np.ndarray]:
    """This function reshapes the input pandas Dataframes to 3D (samples, time, features) numpy arrays

    :param datasets: list of pandas Dataframe
    :return: a tuple of the reshaped datasets as numpy arrays
    """
    for i, dataset in enumerate(datasets):
        datasets[i] = dataset.values.reshape(len(dataset.index.get_level_values(0).unique()),
                                         len(dataset.index.get_level_values(1).unique()),
                                         dataset.shape[1])
    return datasets

def get_sets_shapes(training: np.ndarray, test: np.ndarray) -> pd.DataFrame:
    """This function returns a dataframe with the shapes of the datasets

    :param training: the training dataset numpy array
    :param test: the test dataset numpy array
    :return: dataframe with the shapes of the datasets
    """
    shapes = [training.shape, test.shape]
    shapes = pd.DataFrame(shapes, index=["training dataset", "test dataset"],
                          columns=["nb_items", "nb_timestamps", "nb_features"])
    return shapes