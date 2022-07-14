# Import necessary libraries

from pathlib import Path
import streamlit as st
from PIL import Image
import pandas as pd
import sys
import pickle

sys.path.append("..")

from lib.multiapp import MultiPage
from lib.page_functions import load_image, set_png_as_page_bg


DataFolder = Path("./assets/")
# Load the model once created
# model = pickle.load(open("filename", "rb"))

# Show the header image
# Reference : https://www.youtube.com/watch?v=vwFR2bXXzTw
# Reference for loading model:https://www.youtube.com/watch?v=M1uyH-DzjGE


def read_user_file(csv_file):
    df = pd.read_csv(csv_file)
    return df


def predict_target(df: pd.DataFrame):
    return None


def app():

    """
        This function in this page is run when the page is invoked in the sidebar
    """

    project_image = load_image("page_header.jpg")
    st.image(project_image, use_column_width=True)

    # Project Proposal
    ###########################################
    st.subheader("Supervised Learning", anchor="supervised_learning")

    csv_file = st.file_uploader(
        "Upload CSV file containg township range features", ["csv"]
    )
    if csv_file is not None:
        file_details = {
            "file_name": csv_file.name,
            "file_type": csv_file.type,
            "file_size": csv_file.size,
        }
        st.write("Received File:")
        st.write(file_details)
        df = read_user_file(csv_file)
        st.dataframe(df)

    if st.button("Predict"):
        predicted_depth = predict_target(df)
        st.write("Predict water depth")
    st.markdown("""---""")
