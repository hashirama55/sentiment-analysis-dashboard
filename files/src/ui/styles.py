import streamlit as st
from src.constants import CSS_STYLE

def apply_custom_styles():
    st.markdown(CSS_STYLE, unsafe_allow_html=True)
