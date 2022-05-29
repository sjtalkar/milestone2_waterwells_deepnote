import pandas as pd


def predict_score_base_regressors(reg, X:pd.DataFrame, y:pd.Series, name_of_regressor:str):
    reg.fit(X,y)
    print(f"Prediction from {name_of_regressor} is : {reg.predict(X)}")
    print(f"Train Set Regression Score from {name_of_regressor} is : {reg.score(X,y)}")
    
