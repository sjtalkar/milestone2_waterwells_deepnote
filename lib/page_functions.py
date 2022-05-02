from pathlib import Path
import streamlit as st
from PIL import Image

def load_image(img_name):
       img_path = f"./images/{img_name}"
       image = Image.open(f"./images/{img_name}")
       return image
    