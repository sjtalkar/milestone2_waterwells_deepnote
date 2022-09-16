import sys
sys.path.append('..')

import os
import shap
import pickle
import tempfile
import shap
from IPython.core.display import display, HTML


def shap_deepnote_show(plot):
    tmp_output_filename = tempfile.NamedTemporaryFile(suffix='.html').name
    shap.save_html(tmp_output_filename, plot)

    f = open(tmp_output_filename, "r")
    data = f.read()
    display(HTML(data))

def get_explainer_shap(model, data):
    print(type(model).__name__)
    explainer = shap.Explainer( model)
    shap_values = explainer.shap_values(data)
    return explainer, shap_values

def get_kernel_explainer_shap(model, data):
    print(type(model).__name__)
    explainer = shap.KernelExplainer( model.predict, data)
    shap_values = explainer.shap_values(data)
    return explainer, shap_values

def get_tree_explainer_shap(model, data):
    print(type(model).__name__)
    explainer = shap.TreeExplainer( model)
    shap_values = explainer.shap_values(data)
    return explainer, shap_values
    
def create_over_under_pred(model, y_pred, explainer, X_test_impute_df):
    regressor_name = type(model.best_estimator_.regressor_).__name__ 
    under_prediction = X_test_impute_df.loc[[y_pred.iloc[0].name]]
    over_prediction = X_test_impute_df.loc[[y_pred.iloc[y_pred.shape[0]-1].name]]

    under_prediction_values  =  X_test_impute_df.loc[[y_pred.iloc[0].name]].values
    over_prediction_values  =  X_test_impute_df.loc[[y_pred.iloc[y_pred.shape[0]-1].name]].values

    under_prediction_shap_values = explainer.shap_values(under_prediction)
    over_prediction_shap_values = explainer.shap_values(over_prediction)

    print(f"Model : {regressor_name} under prediction")
    plot = shap.force_plot(explainer.expected_value, under_prediction_shap_values, under_prediction_shap_values, feature_names=X_test_impute_df.columns)
    shap_deepnote_show(plot)

    print(f"Model : {regressor_name} under prediction")
    plot = shap.force_plot(explainer.expected_value, over_prediction_shap_values, over_prediction_shap_values, feature_names=X_test_impute_df.columns)
    shap_deepnote_show(plot)