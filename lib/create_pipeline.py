import sys
sys.path.append('..')

import os
import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.utils.validation import check_is_fitted
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, make_pipeline, FeatureUnion
from sklearn.compose import make_column_transformer, make_column_selector

from sklearn import set_config
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, FunctionTransformer, MinMaxScaler

from lib.transform_impute import convert_scaled_array_to_df, get_column_names_after_transform, convert_back_df, fill_from_prev_year, fill_pop_from_prev_year, PandasSimpleImputer, GroupImputer


def create_transformation_cols(X:pd.DataFrame):

    """This function creates a list of columns that will undergo column transformation
      
        :param X: dataframe to be  transformed
        :output(s): list of columns on which ColumnTransformation is to be applied
    """

    # Set column lists for each transformer to work on

    veg_cols = [
        col for col in X.columns if col.startswith("VEGETATION_")
    ]  
    soil_cols = [
        col for col in X.columns if col.startswith("SOIL_")
    ]  
    crops_cols = [
        col for col in X.columns if col.startswith("CROP_")
    ]  
    population_cols = ['POPULATION_DENSITY']

    veg_soils_crops_cols =  veg_cols + soil_cols + crops_cols

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

    #Set the columns that go through the ColumnTransformation pipeline
    list_cols_used = wcr_cols + veg_soils_crops_cols + population_cols + pct_cols + gse_cols
    columns_to_transform = {
        "wcr_cols": wcr_cols,
        "veg_soils_crops_cols": veg_soils_crops_cols,
        "population_cols": population_cols,
        "pct_cols": pct_cols,
        "gse_cols": gse_cols,
        "list_cols_used": list_cols_used
    }
    return columns_to_transform



def create_transformation_pipelines(X:pd.DataFrame):

    """This function creates pipelines that will be applied on the train and test datasets
      
        :param X: dataframe to be  transformed
        :output(s): 
    """

    columns_to_transform =  create_transformation_cols(X)
    wcr_cols = columns_to_transform["wcr_cols"]
    veg_soils_crops_cols =  columns_to_transform["veg_soils_crops_cols"]
    population_cols =  columns_to_transform["population_cols"]
    pct_cols = columns_to_transform["pct_cols"]
    gse_cols = columns_to_transform["gse_cols"]
    list_cols_used = columns_to_transform["list_cols_used"]
       
    #Transformations through transformers
    wcr_simple_trans = Pipeline(steps=[
        ("imputer", PandasSimpleImputer(missing_values=np.nan, strategy="constant", fill_value=0))
        ,("scaler", MinMaxScaler())
    ])

    # vegetation column transformer
    veg_soil_crops_trans = FunctionTransformer(fill_from_prev_year,
                                                 kw_args={'cols_to_impute': veg_soils_crops_cols })

    pop_trans = Pipeline(steps=[
        ("imputer", FunctionTransformer(fill_pop_from_prev_year))
        ,("scaler", MinMaxScaler())
    ])                                             

    # pct_of_capacity of a resevoir is set as minimum of future years data per township range
    pct_trans = Pipeline(steps=[
        ("imputer", GroupImputer(group_by_cols=["TOWNSHIP_RANGE"],
                                 impute_for_col="PCT_OF_CAPACITY",
                                 aggregation_func="min"))
        ,("scaler", MinMaxScaler())
    ])


    # groundsurfaceelevation is set as median of TownshipRange data per township range
    gse_trans = Pipeline(steps=[
        ("imputer", GroupImputer(group_by_cols=["TOWNSHIP_RANGE"],
                                 impute_for_col="GROUNDSURFACEELEVATION_AVG",
                                 aggregation_func="median"))
        ,("scaler", MinMaxScaler())
    ])
   
    #Start applying the transformers created above

    # PARALLEL EXECUTION CHALLENGES
    # OVERLAPPING COLUMNS CHALLENGES
    # NUMPY NDARRAY and DATAFRAME CHALLENGES

    #Processor 1 
    cols_transformer = ColumnTransformer(
        transformers=[
            # This will return the wcr_cols as the first cols followed by the rest
            ("wcr", wcr_simple_trans, wcr_cols)
            ,("veg", veg_soil_crops_trans, veg_soils_crops_cols)
            ,("pop", pop_trans, population_cols)
            ,("pct_capacity", pct_trans, pct_cols)
            ,("gse", gse_trans, gse_cols)
        ],
        remainder=MinMaxScaler(),
    )

    #Processor 2  This transformer converts a numpy matrix to dataframe
    back_to_df_trans = Pipeline(
        [
            (
                "back_to_pandas",
                FunctionTransformer(
                    func=lambda X_new: convert_back_df(
                        X_new, cols_transformer, X, list_cols_used
                    )
                ),
            )
        ]
    )

    #Processor 3 Scales numeric features 
    std_scaler_preprocessor = ColumnTransformer(
        transformers=[
            ("numerical", StandardScaler(), make_column_selector(dtype_include=np.number))
        ],
        remainder="passthrough",
    )

    minmax_scaler_preprocessor = ColumnTransformer(
        transformers=[
            ("numerical", MinMaxScaler()
            ,make_column_selector(dtype_include=np.number)
            )
        ],
        remainder="passthrough",
    )
    
    impute_pipe = make_pipeline(cols_transformer, back_to_df_trans)
    return  impute_pipe
