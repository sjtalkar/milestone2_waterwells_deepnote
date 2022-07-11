import numpy as np
import pandas as pd

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from tensorflow import keras
from lib.split_data import train_test_group_time_split


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


def evaluate_forecast(y_test: np.ndarray, yhat: np.ndarray) -> Tuple[float, float, float]:
    """This function evaluates the forecasted values against the actual values and returns the following metrics:
    mean absolute error, mean squared error, root mean squared error

    :param y_test: actual values
    :param yhat: forecasted values
    :return: a tuple of the mean absolute error, mean squared error, root mean squared error
    """
    mse_ = keras.metrics.MeanSquaredError()
    mae_ = keras.metrics.MeanAbsoluteError()
    rmse_ = keras.metrics.RootMeanSquaredError()
    mae = mae_(y_test, yhat).numpy()
    mse = mse_(y_test, yhat).numpy()
    rmse = rmse_(y_test, yhat).numpy()
    return mae, mse, rmse

def reshape_data_to_3d(datasets: List[pd.DataFrame]) -> Tuple[np.ndarray, np.ndarray]:
    """This function reshapes the input pandas Dataframes to 3D (samples, time, features) numpy arrays

    :param datasets: list of pandas Dataframe
    :return: a tuple of the reshaped datasets as numpy arrays
    """
    np_datasets = []
    for i, dataset in enumerate(datasets):
        np_datasets.append(dataset.values.reshape(len(dataset.index.get_level_values(0).unique()),
                                                  len(dataset.index.get_level_values(1).unique()),
                                                  dataset.shape[1]))
    return np_datasets

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

def get_train_test_datasets(X: pd.DataFrame, target_variable: str, test_size: int, random_seed: int = 0) -> \
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
    """This function splits the input pandas Dataframe into training and test datasets, applies the impute pipeline
    transformation and reshapes the datasets to 3D (samples, time, features) numpy arrays. The function also returns the
     mpute pipeline fit on the training dataset and the scaler used to transform the target variable.

    :param X: dataframe to be split into training and test datasets
    :param target_variable: the name of the target variable
    :param test_size: size of the test dataset
    :param random_seed: random seed for the train_test_split
    :return: a tuple of the training, test, training_labels, test_labels datasets as numpy arrays, the impute pipeline
    fit on the training dataset and the scaler used to transform the target variable"""
    X_train_df, X_test_df, y_train_df, y_test_df = train_test_group_time_split(X, index=["TOWNSHIP_RANGE", "YEAR"],
        group="TOWNSHIP_RANGE", test_size=test_size, random_seed=random_seed)
    # Create, fit and apply the data imputation pipeline to the training and test sets
    impute_pipeline, columns = create_transformation_pipelines(X_train_df)
    X_train_impute = impute_pipeline.fit_transform(X_train_df)
    X_test_impute = impute_pipeline.transform(X_test_df)
    # Convert the X_train and X_test back to dataframes
    X_train_impute_df = pd.DataFrame(X_train_impute, index=X_train_df.index, columns=columns)
    X_test_impute_df = pd.DataFrame(X_test_impute, index=X_test_df.index, columns=columns)
    # Keep only the target_variable variable as the outcome variable
    target_scaler = MinMaxScaler()
    y_train = target_scaler.fit_transform(y_train_df[[target_variable]])
    y_test = y_test_df[target_variable].to_numpy()
    X_train, X_test = reshape_data_to_3d([X_train_impute_df, X_test_impute_df])
    return X_train, X_test, y_train, y_test, impute_pipeline, target_scaler

def get_data_for_prediction(X: pd.DataFrame, impute_pipeline: Pipeline) -> np.ndarray:
    """This function applies the impute pipeline transformation to the input pandas Dataframe and reshapes the dataset to
    3D (samples, time, features) numpy arrays.

    :param X: dataframe to be transformed
    :param impute_pipeline: the impute pipeline fit on the training dataset
    :return: the transformed dataset as numpy array"""
    X_impute = impute_pipeline.transform(X)
    X_impute_df = pd.DataFrame(X_impute, index=X.index, columns=X.columns)
    X_impute_df.drop("2014", axis=0, level=1, inplace=True)
    X_impute_reshaped = reshape_data_to_3d([X_impute_df])[0]
    return X_impute_reshaped

def combine_all_target_years(X: pd.DataFrame, target_variable: str, predictions: pd.DataFrame) -> pd.DataFrame:
    """This function combines the data of the target variables for the existing years with the predictions into a
    single dataframe.

    :param X: dataframe with the data of the target variables for the existing years
    :param target_variable: the name of the target variable
    :param predictions: the predictions as a Pandas DataFrame
    :return: the combined dataframe
    """
    # Convert the numpy array as a Dataframe with TOWNSHIP_RANGE, YEAR index
    predictions_df = predictions.copy()
    predictions_df["YEAR"] = "2022"
    predictions_df.reset_index(inplace=True)
    predictions_df.set_index(['TOWNSHIP_RANGE', 'YEAR'], drop=True, inplace=True)
    # Get the 2021 values from the data
    all_years_df = X.copy()
    all_years_df = all_years_df[[target_variable]]
    # Append the 2022 predictions
    all_years_df = pd.concat([all_years_df, predictions_df], axis=0)
    all_years_df.sort_index(level=["TOWNSHIP_RANGE", "YEAR"], inplace=True)
    return all_years_df

def get_year_to_year_differences(X: pd.DataFrame, target_variable: str, predictions: pd.DataFrame) -> pd.DataFrame:
    """This functions returns the target variable difference year-to-year between all the years and also between the
    last year and the predicted year.

    :param X: the input dataframe
    :param target_variable: the name of the target variable
    :param predictions: the predictions as a Pandas DataFrame
    :return: a dataframe with the target variable difference year-to-year between all the years and also between the
    last year and the predicted year"""
    difference_df = X.copy()
    predictions_df = predictions.copy()
    # Get the target variable for every year as a column
    difference_df = difference_df[[target_variable]]
    difference_df = difference_df.unstack()
    difference_df.columns = ["_".join(a) for a in difference_df.columns.to_flat_index()]
    # Add the prediction for the following year
    predictions_df.rename(columns={target_variable: "_".join([target_variable, "2022"])}, inplace=True)
    difference_df = difference_df.merge(predictions, left_index=True, right_index=True)
    years = list(X.index.get_level_values(1).unique()) + ["2022"]
    years.sort()
    feature_col = list(difference_df.columns.get_level_values(0))
    for i, year in enumerate(years):
        if i == len(years) - 1:
            break
        difference_df[f"{year}_{years[i+1]}"] = difference_df[f"{target_variable}_{years[i+1]}"] - \
                                             difference_df[f"{target_variable}_{years[i]}"]
    difference_df.drop(columns=feature_col, inplace=True)
    return difference_df