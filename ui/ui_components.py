# ui_components.py

import streamlit as st

def apply_custom_css():
    with open("ui/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
