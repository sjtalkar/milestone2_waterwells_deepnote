# Import necessary libraries

import pandas as pd
import numpy as np
import base64
import re
import time

import altair as alt
from pathlib import Path
import streamlit as st
from PIL import Image

import sys
sys.path.append('..')

from lib.multiapp import MultiPage
from lib.page_functions import load_image

from pages import motivation, datasets, supervised_learning, unsupervised_learning, deeplearning

DataFolder = Path("./assets/")

# Set streamlit page to wide format
st.set_page_config(layout="wide")


#The header above will be followed by each page
app = MultiPage()

#Every page is a py file and has a function app()
app.add_page("Motivation", motivation.app)
app.add_page("Datasets", datasets.app)
app.add_page("Supervised Learning", supervised_learning.app)
app.add_page("Unsupervised Learning", unsupervised_learning.app)
app.add_page("Deeplearning", deeplearning.app)


app.run()