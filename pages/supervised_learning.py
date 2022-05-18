# Import necessary libraries

from pathlib import Path
import streamlit as st
from PIL import Image

import sys
sys.path.append('..')

from lib.multiapp import MultiPage
from lib.page_functions import load_image, set_png_as_page_bg



DataFolder = Path("./assets/")

# Show the header image

def app():

    """
        This function in this page is run when the page is invoked in the sidebar
    """
    
    project_image = load_image("page_header.jpg")
    st.image(project_image, use_column_width=True)

    # Project Proposal
    ###########################################
    st.subheader(
        "Supervised Learning",
        anchor="supervised_learning"
    )


    st.markdown("""---""")
