# Import necessary libraries

import os
import sys
import pickle
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from pathlib import Path
from streamlit_folium import folium_static 

sys.path.append("..")

from lib.multiapp import MultiPage
from lib.page_functions import load_image, set_png_as_page_bg
from lib.prediction_visualization import get_lstm_prediction_df, draw_predictions_for_model


DataFolder = Path("./assets/")
# Load the model once created
# model = pickle.load(open("filename", "rb"))

# Show the header image
# Reference : https://www.youtube.com/watch?v=vwFR2bXXzTw
# Reference for loading model:https://www.youtube.com/watch?v=M1uyH-DzjGE



def app():
    """
        This function in this page is run when the page is invoked in the sidebar
    """
    y_pred_df = None
    project_image = load_image("page_header.jpg")
    st.image(project_image, use_column_width=True)

    # Project Proposal
    ###########################################
    st.subheader("Deeplearning", anchor="deeplearning")
           
    y_pred_df = get_lstm_prediction_df()
    counties_list = list(y_pred_df.COUNTY.unique())
           
    county_selected  = st.selectbox(
                        'Predict for county:',
                         ['All'] + counties_list)
    
    new_y_pred_df = y_pred_df.copy()
    if county_selected != 'All':
        new_y_pred_df['GSE_GWE'] = np.where(new_y_pred_df['COUNTY'] != county_selected, 0, new_y_pred_df['GSE_GWE'])
    
    if st.button("Predict"):
            st.subheader(f"Groundwater Depth Predictions From LSTM")
            st.caption(f"Township-Ranges in San Joaquin river basin")
            st.caption(f"County: {county_selected}")
            st.markdown("""---""")
            folium_static(new_y_pred_df.explore(column='GSE_GWE', cmap='twilight_r'))
            st.markdown("""---""")
            #Streamlit cannot deal with geometry column
            new_df = new_y_pred_df.drop(columns=['geometry'])
            st.dataframe(new_df.loc[new_y_pred_df['COUNTY'] == county_selected][['COUNTY', 'TOWNSHIP_RANGE', 'YEAR', 'GSE_GWE']])
        
    st.markdown("""---""")
