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


    # Project Proposal
    ###########################################
    st.subheader(
        "Supervised Learning",
        anchor="supervised_learning"
    )


    st.markdown("""---""")
