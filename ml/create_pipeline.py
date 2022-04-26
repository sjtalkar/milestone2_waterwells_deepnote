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


from transform_impute import *
from ml.transform_impute import PandasSimpleImputer, GroupImputer



def create_transformation_cols(X:pd.DataFrame):

    """This function creates a list of columns that will undergo column transformation
      
        :param X: dataframe to be  transformed
        :output(s): list of columns on which ColumnTransformation is to be applied
    """

    # Set column lists for each transformer to work on

    veg_cols = [
        col for col in X.columns if "VEGETATION_" in col
    ]  

    soil_cols = [
        col for col in X.columns if "SOIL_" in col
    ]  

    crops_cols = [
        col for col in X.columns if "CROP_" in col and col not in soil_cols
    ]  
    population_cols = ['POPULATION_DENSITY']

    veg_soils_crops_pop_cols = ["TOWNSHIP_RANGE", "YEAR"] + veg_cols + crops_cols + soil_cols +  population_cols

    wcr_cols = [
        "TOTALDRILLDEPTH_AVG",
        "WELLYIELD_AVG",
        "STATICWATERLEVEL_AVG",
        "TOPOFPERFORATEDINTERVAL_AVG",
        "BOTTOMOFPERFORATEDINTERVAL_AVG",
        "TOTALCOMPLETEDDEPTH_AVG",
    ]

    pct_cols = ["TOWNSHIP_RANGE", "PCT_OF_CAPACITY"]

    gse_cols = ["TOWNSHIP_RANGE", "GROUNDSURFACEELEVATION_AVG"]

    # Note that this list depends on the transformation steps preceding the drop and the order in which transformers are called
    drop_cols = [
        "gse_TOWNSHIP_RANGE",
        "pct_capacity_TOWNSHIP_RANGE",
    ]

    #Set the columns that go through the ColumnTransformation pipeline
    list_cols_used = wcr_cols + veg_soils_crops_pop_cols + pct_cols + gse_cols

    return veg_soils_crops_pop_cols, wcr_cols, pct_cols, gse_cols, drop_cols, list_cols_used



def create_transformation_pipelines(X:pd.DataFrame):

    """This function creates pipelines that will be applied on the train and test datasets
      
        :param X: dataframe to be  transformed
        :output(s): 
    """

    veg_soils_crops_pop_cols, wcr_cols, pct_cols, gse_cols, drop_cols, list_cols_used =  create_transformation_cols(X)
       
    #Transformations through transformers
    wcr_simple_trans = PandasSimpleImputer(missing_values=np.nan, strategy="constant", fill_value=0)

    # vegetation column transformer
    veg_soil_crops_pop_trans = FunctionTransformer(fill_from_prev_year, kw_args={'cols_to_impute': veg_soils_crops_pop_cols })

    # pct_of_capacity of a resevoir is set as minimum of future years data per township range
    pct_trans = GroupImputer(
            group_by_cols=["TOWNSHIP_RANGE"],
            impute_for_col="PCT_OF_CAPACITY",
            aggregation_func="min",
        )

    # groundsurfaceelevation is set as mean of TownshipRange data per township range
    gse_trans =  GroupImputer(
            group_by_cols=["TOWNSHIP_RANGE"],
            impute_for_col="GROUNDSURFACEELEVATION_AVG",
            aggregation_func="mean",
        )

   
    #Start applying the transformers created above

    # PARALLEL EXECUTION CHALLENGES
    # OVERLAPPING COLUMNS CHALLENGES
    # NUMPY NDARRAY and DATAFRAME CHALLENGES

    #Processor 1 
    cols_transformer = ColumnTransformer(
        transformers=[
            # This will return the wcr_cols as the first cols followed by the rest
            ("wcr", wcr_simple_trans, wcr_cols)
            # This will return the veg_cols as the first cols followed by the rest
            ,("veg", veg_soil_crops_pop_trans, veg_soils_crops_pop_cols)
            # This will return the township_range and pct_col as the first cols followed by the rest
            ,("pct_capacity", pct_trans, pct_cols)
            # This will return the township_range and gse_col as the first cols followed by the rest
            ,("gse", gse_trans, gse_cols)
        ],
        remainder="passthrough",
    )

    # #Processor 2  This transformer converts a numpy matrix to dataframe
    back_to_df_trans = Pipeline(
        [
            (
                "back_to_pandas",
                FunctionTransformer(
                    func=lambda X_new: convert_back_df(
                        X_new, cols_transformer, X, list_cols_used, drop_cols
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
    impute_scale_pipe = make_pipeline(cols_transformer, back_to_df_trans, minmax_scaler_preprocessor)

    impute_pipe = make_pipeline(cols_transformer, back_to_df_trans)
    
    return  impute_pipe, impute_scale_pipe




