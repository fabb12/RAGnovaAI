# ui_components.py

import streamlit as st

def apply_custom_css():
    """Applica lo stile CSS personalizzato per l'interfaccia utente."""
    st.markdown(
        """
        <style>
        .stTextInput { width: 800px !important; }
        .markdown-container { width: 800px !important; height: 600px !important; overflow: auto; }
        </style>
        """,
        unsafe_allow_html=True
    )
