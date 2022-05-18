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
    
    project_image = load_image("project_motivation.png")
    st.image(project_image, use_column_width=True)
    st.markdown("""---""")

    # Project Proposal
    ###########################################
   
    st.markdown('''<p><strong>There's a whole fascinating world that exists underneath our feet that we don't see, therefore we don't relate.<br>--Erin Brokovich</strong></p>''',  unsafe_allow_html=True)
    st.markdown("""---""")
    
    
    