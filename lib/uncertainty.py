#Reference : https://github.com/WillKoehrsen/Data-Analysis/blob/master/prediction-intervals/prediction_intervals.ipynb


import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import GradientBoostingRegressor
from lib.township_range import TownshipRanges
from lib.supervised_tuning import read_target_shifted_data
from sklearn_quantile import RandomForestQuantileRegressor

class RandomForestPredictionIntervals(BaseEstimator):
    
    def __init__(self, lower_alpha=0.1, upper_alpha=0.9, **kwargs):
        """
        Model that produces prediction intervals with a Scikit-Learn inteface
        
        :param lower_alpha: lower quantile for prediction, default=0.1
        :param upper_alpha: upper quantile for prediction, default=0.9
        :param **kwargs: additional keyword arguments for creating a GradientBoostingRegressor model
        """
        self.random_state = 42
        self.median_alpha = 0.5
        self.lower_alpha = lower_alpha
        self.upper_alpha = upper_alpha
    
    def fit(self, X_train, y_train):
        """
        Fit all three models
            
        :param X: train features
        :param y: train targets
        """
              
        self.qrf = RandomForestQuantileRegressor(q=[self.lower_alpha, self.median_alpha, self.upper_alpha])
        self.qrf.fit(X_train, y_train)

    def predict(self, X, y):
        """
        Predict with all 3 models 
        
        :param X: test features
        :param y: test targets
        :return predictions: dataframe of predictions
        
        """
        y_pred_lower, y_pred_median, y_pred_upper = self.qrf.predict(X)

        predictions = pd.DataFrame(y)
        predictions["lower"] = y_pred_lower
        predictions["mid"] = y_pred_median
        predictions["upper"] = y_pred_upper
        self.predictions = predictions
        return predictions

class GradientBoostingPredictionIntervals(BaseEstimator):
    """
    Model that produces prediction intervals with a Scikit-Learn inteface
    
    :param lower_alpha: lower quantile for prediction, default=0.1
    :param upper_alpha: upper quantile for prediction, default=0.9
    :param **kwargs: additional keyword arguments for creating a GradientBoostingRegressor model
    """

    def __init__(self, lower_alpha=0.1, upper_alpha=0.9, **kwargs):
        self.lower_alpha = lower_alpha
        self.upper_alpha = upper_alpha

        # Three separate models
        self.lower_model = GradientBoostingRegressor(
            loss="quantile", alpha=self.lower_alpha, **kwargs
        )
        self.mid_model = GradientBoostingRegressor(loss="ls", **kwargs)
        self.upper_model = GradientBoostingRegressor(
            loss="quantile", alpha=self.upper_alpha, **kwargs
        )
        self.predictions = None

    def fit(self, X_train, y_train):
        """
        Fit all three models
            
        :param X: train features
        :param y: train targets
        """
        self.lower_model.fit(X_train, y_train)
        self.mid_model.fit(X_train, y_train)
        self.upper_model.fit(X_train, y_train)

    def predict(self, X, y):
        """
        Predict with all 3 models 
        
        :param X: test features
        :param y: test targets
        :return predictions: dataframe of predictions
        
        """
        predictions = pd.DataFrame(y)
        predictions["lower"] = self.lower_model.predict(X)
        predictions["mid"] = self.mid_model.predict(X)
        predictions["upper"] = self.upper_model.predict(X)
        self.predictions = predictions

        return predictions

def create_prediction_uncertainty_gbr():
    RANDOM_SEED = 42
    data_dir = "../assets/train_test_target_shifted/"
    train_test_dict_file_name = "train_test_dict_target_shifted.pickle"
    X_train_df_file_name = "X_train_impute_target_shifted_df.pkl"
    X_test_df_file_name = "X_test_impute_target_shifted_df.pkl"

    train_test_dict, X_train_impute_df, X_test_impute_df = read_target_shifted_data(
        data_dir, train_test_dict_file_name, X_train_df_file_name, X_test_df_file_name
    )
    X_train_impute = train_test_dict["X_train_impute"]
    X_pred_impute = train_test_dict["X_pred_impute"]

    y_train_df = train_test_dict['y_train']
    y_pred_df = train_test_dict['y_pred']


    y_train = y_train_df['GSE_GWE_SHIFTED'].values.ravel()

    gbr = GradientBoostingPredictionIntervals(lower_alpha = 0.05,
                                            upper_alpha = 0.95,
                                            n_estimators = 200,
                                            min_samples_split = 20,
                                            min_samples_leaf=10,
                                            max_depth=2,
                                            learning_rate=0.05,
                                            random_state = RANDOM_SEED)
    gbr.fit(X_train_impute, y_train)
    y_pred_df = gbr.predict(X_pred_impute, y_pred_df)  
    township_range = TownshipRanges()
    county_tr_mapping = township_range.counties_and_trs_df
    y_pred_df = county_tr_mapping.merge(y_pred_df, left_on='TOWNSHIP_RANGE', right_on='TOWNSHIP_RANGE') 
    y_pred_df.drop(columns=['GSE_GWE_SHIFTED'], inplace=True)
    y_pred_df.to_csv("../pages/predicting_uncertainty_gbr.csv", index=False)
    return y_pred_df


def create_prediction_uncertainty_qrf():
    RANDOM_SEED = 42
    data_dir = "../assets/train_test_target_shifted/"
    train_test_dict_file_name = "train_test_dict_target_shifted.pickle"
    X_train_df_file_name = "X_train_impute_target_shifted_df.pkl"
    X_test_df_file_name = "X_test_impute_target_shifted_df.pkl"

    train_test_dict, X_train_impute_df, X_test_impute_df = read_target_shifted_data(
        data_dir, train_test_dict_file_name, X_train_df_file_name, X_test_df_file_name
    )
    X_train_impute = train_test_dict["X_train_impute"]
    X_pred_impute = train_test_dict["X_pred_impute"]

    y_train_df = train_test_dict['y_train']
    y_pred_df = train_test_dict['y_pred']

    y_train = y_train_df['GSE_GWE_SHIFTED'].values.ravel()

    qrf = RandomForestPredictionIntervals(q=[0.05, 0.50, 0.95],
                                         n_estimators=150,
                                         max_depth = 5, 
                                         random_state = RANDOM_SEED)
   

    qrf.fit(X_train_impute, y_train)
    y_pred_df = qrf.predict(X_pred_impute, y_pred_df)

    township_range = TownshipRanges()
    county_tr_mapping = township_range.counties_and_trs_df
    y_pred_df = county_tr_mapping.merge(y_pred_df, left_on='TOWNSHIP_RANGE', right_on='TOWNSHIP_RANGE') 
    y_pred_df.drop(columns=['GSE_GWE_SHIFTED'], inplace=True)
    y_pred_df.to_csv("../pages/predicting_uncertainty_qrf.csv", index=False)
    return y_pred_df

