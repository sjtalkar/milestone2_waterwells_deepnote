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
    st.title(
        "Milestone II Project Proposal ",
        anchor="project_title",
    )
  
    project_image = load_image("page_header.jpg")
    st.image(project_image, use_column_width=True)
    st.markdown("""---""")

    # Project Proposal
    ###########################################
    st.markdown("""
                <style>
                .subtitle-font {
                    font-size:70px 
                }
                </style>
                """, unsafe_allow_html=True)
    
   
    st.markdown('''**There's a whole fascinating world that exists underneath our feet that we don't see, therefore we don't relate.**''')
    st.markdown("***")
   
    st.markdown('''**--Erin Brokovich**''') 
    st.markdown("""---""")
    
    
    