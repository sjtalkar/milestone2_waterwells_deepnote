import pandas as pd
import numpy as np

from math import sqrt
from sklearn.metrics import mean_squared_error
from sklearn.metrics import median_absolute_error, r2_score
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor


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

    
