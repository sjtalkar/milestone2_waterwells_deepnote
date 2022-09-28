import pandas as pd
import numpy as np

import os
import pickle

from math import sqrt
from sklearn.metrics import mean_squared_error, median_absolute_error, r2_score, mean_absolute_error
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.linear_model import LinearRegression
from sklearn.compose import TransformedTargetRegressor
from sklearn.model_selection import RandomizedSearchCV
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Create a feature importance property for the the TransformedTargetRegressor
class FeatureTTRegressor(TransformedTargetRegressor):
    """This class wraps the TransformedTargetRegressor to provide feature_importance property
    """
    
    @property
    def feature_importances_(self):
        return self.regressor_.feature_importances_



def compare_models_manual(base_model_param_dict, X_train_impute, y_train, random_seed, n_iter=50, cv=3):
    """This function creates a list of best models after hyperparametr tuning and returns 
       this list along with a disctionary of the best parameters found
    :param base_model_param_dict: dictionary with model name as key and value that is a list of model constructor and a dictionary of
                                  parameters to hypertune 
    :param X_train_impute: dataframe or numpy array with features
    :param y_train: target labels
    :param random_seed : random seed for reproducibility
    :param n_iter : number of iterations for cross validation
    :param cv : folds of cross validation
    
    :return: models : list of best estimators
             best_params_dict : dictionary of best parameters found for each estimator
    """
    
    models = []
    best_params_dict = {}
    for model_name in base_model_param_dict.keys():
        ## Repeat this for several models
        model_base = base_model_param_dict[model_name][0]
        # Create the parameter grid
        model_grid = base_model_param_dict[model_name][1]

        model_transformed_target = FeatureTTRegressor(regressor=model_base,
                                func=np.sqrt, inverse_func=np.square)                        
        model_best = RandomizedSearchCV(estimator = model_transformed_target,
                                        param_distributions = model_grid,
                                        n_iter = n_iter, cv = cv, verbose = 1, 
                                        random_state = random_seed, n_jobs = -1)


        model_best = model_best.fit(X_train_impute, y_train)
        models.append(model_best)

        best_params_dict[type(model_best.best_estimator_.regressor_).__name__] = model_best.best_params_
    return models, best_params_dict


def final_comparison_sorted(models, test_features, test_labels):
    """This function creates a dataframe to compare models based on mean absolute error,
        mean squared error. root mean squared error, and r-squared

    :param models: list of models with tuned parameters
    :param test_features: dataframe or numpy array with features
    :param test_labels: target labels
    :return: dataframe with the scores for different models sorted (long form)
    """
       
    scores_dict = {}
    for model in models:
        predictions = model.predict(test_features)
        mae = round(mean_absolute_error(test_labels, predictions), 4)
        mse = round(mean_squared_error(test_labels, predictions), 4)
        rmse = round(np.sqrt(mean_squared_error(test_labels, predictions)), 4)
        r2 = round(r2_score(test_labels, predictions), 4)
        scores_dict[type(model.best_estimator_.regressor_).__name__] = [mae, mse, r2, rmse] 

    scores_df = pd.DataFrame.from_dict (scores_dict, orient='index', columns = ['Mean Absolute Error', 'Mean Squared Error', 'R^2', 'RMSE'])
    scores_df.sort_values(by=[ 'R^2', 'Mean Absolute Error'], ascending=False, inplace=True)
    return scores_df



def final_comparison(models, test_features, test_labels):
    """This function creates a dataframe to compare models based on mean absolute error,
        mean squared error. root mean squared error, and r-squared

    :param models: list of models with tuned parameters
    :param test_features: dataframe or numpy array with features
    :param test_labels: target labels
    :return: dataframe with the scores for different models (wide format)
    """
       
    scores = pd.DataFrame()
    for model in models:
        predictions = model.predict(test_features)
        mae = round(mean_absolute_error(test_labels, predictions), 4)
        mse = round(mean_squared_error(test_labels, predictions), 4)
        rmse = round(np.sqrt(mean_squared_error(test_labels, predictions)), 4)
        r2 = round(r2_score(test_labels, predictions), 4)
        scores[type(model.best_estimator_.regressor_).__name__] = [mae, mse, r2, rmse]
    scores.index = ['Mean Absolute Error', 'Mean Squared Error', 'R^2', 'RMSE']
    return scores

def read_target_shifted_data(data_dir: str,
                             train_test_dict_file_name: str,
                             X_train_df_file_name: str,
                             X_test_df_file_name: str):
    """This function creates a dataframe to compare models based on mean absolute error,
        mean squared error. root mean squared error, and r-squared

    :param data_dir: directory containing pickled processed data files
    :param train_test_dict_file_name: file containing train and test numpy arrays
    :param X_train_df_file_name: file containing training feauture dataframe
    :param X_test_df_file_name : file containing testing feauture dataframe
    :return: retrieved dictionary of numpy arrays and dataframess
    """
    full_path = f"{data_dir}{train_test_dict_file_name}"
    with open(full_path, 'rb') as file:
            train_test_dict = pickle.load( file)
    
    full_path = f"{data_dir}{X_train_df_file_name}"
    with open(full_path, 'rb') as file:
            X_train_impute_df = pickle.load( file)

    full_path = f"{data_dir}{X_test_df_file_name}"
    with open(full_path, 'rb') as file:
            X_test_impute_df = pickle.load( file)
    return train_test_dict, X_train_impute_df, X_test_impute_df 


def read_target_shifted_pca_data(data_dir:str,
                                 pca_file_name:str,
                                ):
    """This function creates a dataframe to compare models based on mean absolute error,
        mean squared error. root mean squared error, and r-squared

    :param data_dir: directory containing pickled processed data files
    :param pca_file_name: file containing train and test numpy arrays
    :return: retrieved dictionary of numpy arrays 
    """                            
    data_dir_  = '../assets/train_test_target_shifted/'
    pca_file_name = 'X_target_shifted_pca.pickle'
    full_path = f"{data_dir}{pca_file_name}"
    with open(full_path, 'rb') as file: 
        pca_train_test_dict = pickle.load(file)
    return pca_train_test_dict

def print_scores(reg, X:pd.DataFrame, y_true:pd.Series, name_of_regressor):

    #Since the models are being wrapped in TransformedTargetRegressor,
    # we do not have to perform inverse_transform 
    y_hat = reg.predict(X)
 
    r2 = r2_score(y_true, y_hat)
    mse = mean_squared_error(y_true, y_hat)
    print(f"Scores from {name_of_regressor} : R2 score:{r2};  MSE score:{mse}; RMSE score:{sqrt(mse)}")
    


def predict_mean_squared_error_regression(reg, X:pd.DataFrame, y_true:pd.Series, name_of_regressor):

    #Since the models are being wrapped in TransformedTargetRegressor,
    # we do not have to perform inverse_transform 
    y_hat = reg.predict(X)
 
    print(f"Prediction from {name_of_regressor} is : {y_hat}")
    r2 = r2_score(y_true, y_hat)
    mse = mean_squared_error(y_true, y_hat)
    print(f"Scores from {name_of_regressor} : R2 score:{r2};  MSE score:{mse}; RMSE score:{sqrt(mse)}")
    

def predict_score_base_regressors(reg, X:pd.DataFrame, y:pd.Series, name_of_regressor:str):
    reg.fit(X,y)
    print(f"Prediction from {name_of_regressor} is : {reg.predict(X)}")
    print(f"Train Set Regression Score from {name_of_regressor} is : {reg.score(X,y)}")

def add_cluster_label(X_train_impute_df, X_test_impute_df, n_clusters, random_seed):
    kclf = KMeans(n_clusters = n_clusters, random_state=random_seed)
    kclf.fit(X_train_impute_df.values)

    train_labels = kclf.labels_
    test_labels = kclf.predict(X_test_impute_df.values)


    X_train_cluster_df = X_train_impute_df.copy()
    X_test_cluster_df = X_test_impute_df.copy()

    X_train_cluster_df['km_label'] = train_labels
    X_test_cluster_df['km_label'] = test_labels
    return X_train_cluster_df, X_test_cluster_df 

def get_model_errors():
    """ This function return the evaluation metrics for the top 6 models.
        It also returns the test-target dataframe along with the predicted targets for each of the 
        models.
    :param None
    :return: dataframe with evaluation scores, dataframe with target value and predicted absolute errors
    """

    data_dir = "../assets/train_test_target_shifted/"
    train_test_dict_file_name = "train_test_dict_target_shifted.pickle"
    X_train_df_file_name = "X_train_impute_target_shifted_df.pkl"
    X_test_df_file_name = "X_test_impute_target_shifted_df.pkl"

    train_test_dict, X_train_impute_df, X_test_impute_df = read_target_shifted_data(
        data_dir, train_test_dict_file_name, X_train_df_file_name, X_test_df_file_name
    )
    X_test_impute = train_test_dict["X_test_impute"]
    y_test_df = train_test_dict["y_test"]
    y_test = y_test_df["GSE_GWE_SHIFTED"].values.ravel()

    test_year_list = list(X_test_impute_df.index.get_level_values("YEAR").unique())
    with open("../assets/models/supervised_learning_models/models.pickle", "rb") as file:
        models = pickle.load(file)


    test_model_errors_df = final_comparison_sorted(models, X_test_impute, y_test)
    test_model_errors_df.to_csv("../test_model_errors.csv", index=False)

    for model in models:
        regressor_name = type(model.best_estimator_.regressor_).__name__
        y_test_df[regressor_name] = model.best_estimator_.predict(X_test_impute)
        y_test_df[f'{regressor_name}_absolute_error'] = np.abs(y_test_df[regressor_name] - y_test_df['GSE_GWE_SHIFTED'])

    y_test_df = y_test_df.reset_index()
    col_subset = [
        col
        for col in y_test_df.columns
        if col.endswith("_absolute_error") or "TOWNSHIP_RANGE" in col or "GSE_GWE" in col
    ]
    y_test_df = y_test_df[col_subset]
    melt_cols = [col for col in y_test_df.columns if col.endswith("_absolute_error")]
    error_df = y_test_df.melt(
        id_vars=["TOWNSHIP_RANGE", "GSE_GWE_SHIFTED"],
        value_vars=melt_cols,
        var_name="model_name",
        value_name="absolute_error",
    )

    return test_model_errors_df, error_df

def get_supervised_models_predictions():
    """ This function return the predictions of the supervised learning models.
    :param None
    :return: dataframe with evaluation scores, dataframe with target value and predicted absolute errors
    """

    data_dir = "../assets/train_test_target_shifted/"
    train_test_dict_file_name = "train_test_dict_target_shifted.pickle"
    X_train_df_file_name = "X_train_impute_target_shifted_df.pkl"
    X_test_df_file_name = "X_test_impute_target_shifted_df.pkl"

    train_test_dict, X_train_impute_df, X_test_impute_df = read_target_shifted_data(
        data_dir, train_test_dict_file_name, X_train_df_file_name, X_test_df_file_name
    )
    X_test_impute = train_test_dict["X_test_impute"]
    y_test_df = train_test_dict["y_test"]
    y_test = y_test_df["GSE_GWE_SHIFTED"].values.ravel()

    test_year_list = list(X_test_impute_df.index.get_level_values("YEAR").unique())
    with open("../assets/models/supervised_learning_models/models.pickle", "rb") as file:
        models = pickle.load(file)


    test_model_errors_df = final_comparison_sorted(models, X_test_impute, y_test)
    test_model_errors_df.reset_index(drop=False, inplace=True)
    test_model_errors_df.rename(columns={"index": "MODEL"}, inplace=True)

    for model in models:
        regressor_name = type(model.best_estimator_.regressor_).__name__
        y_test_df[regressor_name] = model.best_estimator_.predict(X_test_impute)

    y_test_df = y_test_df.reset_index()
    y_test_df.rename(columns={"GSE_GWE_SHIFTED": "2021_GSE_GWE"}, inplace=True)
    y_test_df.drop(columns=["YEAR"], inplace=True)

    return test_model_errors_df, y_test_df
