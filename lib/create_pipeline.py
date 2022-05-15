import numpy as np
import pandas as pd

from typing import List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit, TimeSeriesSplit

from lib.transform_impute import GroupImputer, PandasSimpleImputer, estimate_pop_from_prev_year, fill_from_prev_year

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