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

# Define a function that compares all final models DO THIS FOR SVM and XGBOOST
def final_comparison(models, test_features, test_labels):
    """This function creates a dataframe to compare models based on mean absolute error,
        mean squared error. root mean squared error, and r-squared

    :param models: list of models with tuned parameters
    :param test_features: dataframe or numpy array with features
    :param test_labels: target labels
    :return: dataframe with the scores for different models
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

def read_target_shifted_data(data_dir:str,
                             train_test_dict_file_name:str,
                             X_train_df_file_name:str,
                             X_test_df_file_name:str):
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
    
    full_path =  f"{data_dir}{X_train_df_file_name}"
    with open(full_path, 'rb') as file:
            X_train_impute_df = pickle.load( file)

    full_path =  f"{data_dir}{X_test_df_file_name}"
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

    
