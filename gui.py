import streamlit as st
import json
import requests
from PIL import Image

# Add a list of supported cities.
supported_cities = ["Tampa"]
st.title("Facebook scraper")

if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

def toggle_button():
    st.session_state.button_clicked = not st.session_state.button_clicked

button_label = "Stop" if st.session_state.button_clicked else "Start"
if st.button(button_label):
    toggle_button()
    if st.session_state.button_clicked:

        res = requests.get(f"http://0.0.0.0:4000/")
    else:
        pass
    

      


