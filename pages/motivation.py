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
    st.title(
        "Milestone II Project Proposal ",
        anchor="project_title",
    )
    
    st.header(
        "A Thirsty Valley",
        anchor="project_subtitle",
    )
  

    st.markdown('''**Aim:** Create measurable objective of sustainability''')  
    st.markdown('''California's Sustainable Groundwater Management Act (SGMA) was passed in 2014 with the intention to address over pumping, halt chronic water-level declines and bring long-depleted aquifers into balance. Despite SGMA, a frenzy of well drilling has continued on large farms across **the San Joaquin Valley, the state's largest and most lucrative agricultural zone** As a result, shallower wells supplying nearly a thousand family homes have gone dry in recent years.''')  
    st.markdown('''Frequently, perniciously drought-inflicted California, depends on groundwater for a major portion of its annual water supply, particularly for agricultural and domestic usage. This project seeks to aid policy makers preemptively identify areas prone to overdraft and bring groundwater basins into **balanced levels of pumping and recharge.**''')
    st.markdown('''Focused on the San Joaquin Valley, the objectives are:''')
    st.markdown('''
        - **Supervised Learning:** Predict the depth to groundwater elevation in feet below ground surface (GSE_GWE). This value portends shortage in a TownshipRange. Increase or decrease in GSE_GWE will then indicate if there will be more requests for well construction. This in turn will provide a quantitative metric for whether SGMA is functioning and areas to focus on for recharge.
        - **Unsupervised Learning:** cluster areas into sustainable and unsustainable areas, anomaly detection''')            
              
    st.markdown('''The geographical unit of analysis chosen for this project is the Township-Range level of the [Public Land Survey System](https://en.wikipedia.org/wiki/Public_Land_Survey_System)''')
    st.markdown("***")
    st.subheader("The Datasets")
    st.markdown('''We have collected 10 geospatial datasets from different government agencies for the 2014-2021 period, on the topics impacting water consumption:''')  
              
    st.markdown('''Geo-spatial data (San Joaquin Valley PLSS), current groundwater levels and consumption through well completion reports, recharge factors and consumption factors through precipitation, water reservoir capacity, agricultural crops, population density, regional vegetation, soils survey and water shortages reports.''')
    st.markdown(''' Basic GeoPandas ETL operations to aggregate data at TownshipRange level were followed up with pipelines, leveraged to impute missing values, normalize and scale data appropriately.''')   
    
    st.markdown('''
        - Use Voronoi diagrams to estimate area value from point measurement (e.g precipitation reading from measurement station is used to infer TownshipRange precipitation
        - Aggregate counts or measures at the Township-Range level (e.g. the count of well shortage reports)
        - Overlay Township-Range boundaries on geospatial data to estimate Township-Range values (e.g. estimate the percentage of land use for different type of agriculture crops)
        - Data imputation, feature scaling and feature dimensionality reduction are performed on the aggregated data (where applicable)  before doing supervised and unsupervised learning.
        ''')  
    st.markdown('''The post ETL dataset used for supervised and unsupervised learning is a multi-time-series (one 2014 to 2021 time series per Township-Range)  multivariate (each Township-Range time series has many variables) dataset.''')

    st.subheader("Supervised Machine Learning")
    st.markdown('''
            - Set baseline with Dummy Regressor
            - Regression : Evaluation using RMSE, R2, MAE
            - GridSearchCV/RandomSearchCV to tune parameters
            - Check for over-fitting and regularization
            - Will use PCA (unsupervised technique) to reduce features to aid the regression task, biplot visualization to enhance understanding of latent dimensions, scree plot for selection.
            - Will use K Means clustering (unsupervised technique) for feature engineering. 
            - Will compare tree and forest regressors with linear regression algorithms. The former is not sensitive to unnormalized and unscaled data
            - Will apply Lasso regression (also aids in feature selection by setting low coefficients) and Ridge regression
            - Identify important features using Shapely
            ''')
 
    st.subheader("Unsupervised Machine Learning")
    st.markdown('''
            - Top-down, expectation maximization technique K-Means clustering (pre-defined- number of clusters), 
            - Hierarchical, Bottom-up technique : Agglomerative clustering (dendogram visualization)
            - Outlier detection friendly clustering (DBSCAN) to mediate an emergency situation.
            - Evaluation of inter and intra cluster scores using cost functions.
            ''')
    
    st.subheader("The Team and Contribution")
    st.markdown('''Both Simi Talkar and Matthieu Lienart have participated to all aspects of the project.''')
    st.subheader("The Timeline:")
    st.markdown('''
            - January to April 2022: Datasets collection and ETL
            - May to August 2022: Data imputation, feature dimensionality reduction, supervised and unsupervised learning
            - September, October 2022: Write report
            ''')
    
    st.subheader("Appendix:")

    st.markdown('''**Sustainable groundwater management** is defined as managing water supplies in a way that can be maintained without "causing undesirable results," such as chronic declines in groundwater levels or “significant and unreasonable” depletion, adverse effects on surface water, degraded water quality or land subsidence.''')
    
    st.markdown("**Drought Years**")
    drought_image = load_image("drought_years_california.png")
    st.image(drought_image, caption="Drought Years In California",  use_column_width=True)
   
    st.markdown("**Dataset**")
    dataset_image = load_image("groundwater_modeling.png")
    st.image(dataset_image, caption="Groundwater Dataset Modeling",use_column_width=True)
    