from pathlib import Path
import streamlit as st
from PIL import Image
import base64

def load_image(img_name):
    img_path = f"./images/{img_name}"
    image = Image.open(f"./images/{img_name}")
    return image

def set_bg_image_url():
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''
    
    #background: url("https://cdn.pixabay.com/photo/2020/06/19/22/33/wormhole-5319067_960_720.jpg");
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url("https://github.com/sjtalkar/milestone2_waterwells_deepnote/blob/master/images/vertical_bubbles.jpg");
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )


@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    body {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return
