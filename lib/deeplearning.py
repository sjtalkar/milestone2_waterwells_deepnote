import os
import numpy as np
import pandas as pd
import pickle

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler

from tensorflow import keras

from lib.split_data import train_test_group_time_split, train_test_time_split
from lib.transform_impute import fill_from_prev_year, fill_pop_from_prev_year


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

    # Set the columns that go through the ColumnTransformation pipeline
    list_cols_used = wcr_cols + veg_soils_crops_cols + population_cols + pct_cols + gse_cols
    columns_to_transform = {
        "wcr": wcr_cols,
        "veg_soils_crops": veg_soils_crops_cols,
        "pop": population_cols,
        "pct": pct_cols,
        "gse": gse_cols,
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
        ("imputer", FunctionTransformer(fill_from_prev_year))
    ])
    pop_trans = Pipeline(steps=[
        ("imputer", FunctionTransformer(fill_pop_from_prev_year)),
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
            ("veg_soils_crops", veg_soil_crops_trans, columns_to_transform["veg_soils_crops"]),
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


def get_train_test_datasets(X: pd.DataFrame, target_variable: str, test_size: int, random_seed: int = 0,
                            save_to_file: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                                                                 Pipeline, List[str], MinMaxScaler]:
    """This function splits the input pandas Dataframe into training and test datasets, applies the impute pipeline
    transformation and reshapes the datasets to 3D (samples, time, features) numpy arrays. The function also returns the
     mpute pipeline fit on the training dataset and the scaler used to transform the target variable.

    :param X: dataframe to be split into training and test datasets
    :param target_variable: the name of the target variable
    :param test_size: size of the test dataset
    :param random_seed: random seed for the train_test_split
    :return: a tuple of the training, test, training_labels, test_labels datasets as numpy arrays, the impute pipeline
    fit on the training dataset, the columns names in the order they are modified by the imputation pipeline and the
    scaler used to transform the target variable"""
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
    # Save the train test X and y datasets as a pickle file
    train_test_dict = {
        "X_train": X_train_impute_df,
        "X_test": X_test_impute_df,
        "y_train": y_train_df[[target_variable]],
        "y_test": y_test_df[[target_variable]],
    }
    if save_to_file:
        dataset_dir = "../assets/train_test/"
        os.makedirs(os.path.dirname(dataset_dir), exist_ok=True)
        with open(os.path.join(dataset_dir, "dl_train_test.pkl"), "wb") as file:
            pickle.dump(train_test_dict, file)
    return X_train, X_test, y_train, y_test, impute_pipeline, columns, target_scaler


def get_train_test_datasets_with_2021_as_target(X: pd.DataFrame, target_variable: str) -> \
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Pipeline, List[str], MinMaxScaler]:
    """This function splits the input pandas Dataframe into training and test datasets, applies the impute pipeline
    transformation and reshapes the datasets to 3D (samples, time, features) numpy arrays. The function also returns the
     mpute pipeline fit on the training dataset and the scaler used to transform the target variable.

    :param X: dataframe to be split into training and test datasets
    :param target_variable: the name of the target variable
    :return: a tuple of the training, test, training_labels, test_labels datasets as numpy arrays, the impute pipeline
    fit on the training dataset, the columns names in the order they are modified by the imputation pipeline and the
    scaler used to transform the target variable"""

    # We get the X and y test data from the 2015 to 2021 data
    # The 2015-2020 are the X training data and the 2021 is the y target
    X_test_df, y_test_df = train_test_time_split(X, index=["TOWNSHIP_RANGE", "YEAR"], group="TOWNSHIP_RANGE")
    y_test_df = y_test_df[[target_variable]]
    # We get the X and y training data from the 2014 to 2020 data
    # The 2014-2019 are the X training data and the 2020 is the y target
    X_train_df, y_train_df = train_test_time_split(X.drop("2021", level=1, axis=0), index=["TOWNSHIP_RANGE", "YEAR"],
                                                  group="TOWNSHIP_RANGE")
    y_train_df = y_train_df[[target_variable]]
    # Create, fit and apply the data imputation pipeline to the training and test sets
    impute_pipeline, columns = create_transformation_pipelines(X_train_df)
    X_train_impute = impute_pipeline.fit_transform(X_train_df)
    X_test_impute = impute_pipeline.transform(X_test_df)
    # Convert the X_train and X_test back to dataframes
    X_train_impute_df = pd.DataFrame(X_train_impute, index=X_train_df.index, columns=columns)
    X_test_impute_df = pd.DataFrame(X_test_impute, index=X_test_df.index, columns=columns)
    X_test_impute_df.drop("2014", level=1, axis=0, inplace=True)
    # Keep only the target_variable variable as the outcome variable
    target_scaler = MinMaxScaler()
    y_train = target_scaler.fit_transform(y_train_df[[target_variable]])
    y_test = y_test_df[target_variable].to_numpy()
    X_train, X_test = reshape_data_to_3d([X_train_impute_df, X_test_impute_df])
    # Save the train test X and y datasets as a pickle file
    train_test_dict = {
        "X_train": X_train_impute_df,
        "X_test": X_test_impute_df,
        "y_train": y_train_df[[target_variable]],
        "y_test": y_test_df[[target_variable]],
    }
    return X_train, X_test, y_train, y_test, impute_pipeline, columns, target_scaler


def get_data_for_prediction(X: pd.DataFrame, impute_pipeline: Pipeline, impute_columns: List[str]) -> np.ndarray:
    """This function applies the impute pipeline transformation to the input pandas Dataframe and reshapes the dataset to
    3D (samples, time, features) numpy arrays.

    :param X: dataframe to be transformed
    :param impute_pipeline: the impute pipeline fit on the training dataset
    :param impute_columns: the columns names in the order they are modified by the imputation pipeline
    :return: the transformed dataset as numpy array"""
    x_impute = impute_pipeline.transform(X)
    x_impute_df = pd.DataFrame(x_impute, index=X.index, columns=impute_columns)
    x_impute_df.drop("2014", axis=0, level=1, inplace=True)
    x_impute_reshaped = reshape_data_to_3d([x_impute_df])[0]
    return x_impute_reshaped


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
    difference_df = difference_df.merge(predictions_df, left_index=True, right_index=True)
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
