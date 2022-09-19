# Import necessary libraries



from pathlib import Path
import streamlit as st
from PIL import Image

import sys
sys.path.append('..')

from lib.multiapp import MultiPage
from lib.page_functions import load_image



DataFolder = Path("./assets/")

# Show the header image

def app():

    """
        This function in this page is run when the page is invoked in the sidebar
    """    
    project_image = load_image("page_header.jpg")
    st.image(project_image, use_column_width=True)
    st.subheader(
        "Datasets",
        anchor="datasets"
     
    )

    dataset_image = load_image("groundwater_modeling.png")
    st.image(dataset_image, use_column_width=True)
    
    st.markdown(
        """
        **The Datasets**
        We have collected 10 geospatial datasets from federal and state (CA) government agencies for the 2014-2021 period, on the factors impacting groundwater depth: 
        Geo-spatial data (San Joaquin Valley PLSS), current groundwater levels and consumption through well completion reports, agricultural crops, population density, regional vegetation and water shortages reports, water reservoir capacity, recharge through precipitation and soils survey (see Appendix 3).

        Basic GeoPandas ETL operations to aggregate data at TownshipRange level were followed up with pipelines, leveraged to impute missing values, normalize and scale data appropriately.
        Use Voronoi diagrams to estimate area value from point measurement (e.g precipitation reading from measurement station is used to infer Township-Range precipitation)
        Aggregate features at common granularity of Township-Range and Year with appropriate estimation.
        Data imputation, feature scaling and feature dimensionality reduction are performed using pipelines before doing supervised and unsupervised learning.
        The post ETL dataset used for supervised and unsupervised learning is a multi-indexed, multivariate time series dataset (where each Township-Range index with independent variables is a 2014 to 2021 time series).

        """
        
    )
    st.markdown("""---""")

