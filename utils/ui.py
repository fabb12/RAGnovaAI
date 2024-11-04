import streamlit as st

def display_interface():
    st.title("Help Desk AI - Master Finance -")
    st.sidebar.header("Carica il tuo documento")
    uploaded_file = st.sidebar.file_uploader("Scegli un file", type=['pdf', 'docx', 'txt'])
    return uploaded_file
