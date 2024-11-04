# ui_components.py

import streamlit as st
import os
import subprocess
from document_manager import delete_document

def display_sidebar_documents(document_names, vector_store):
    """Mostra i documenti nella barra laterale con opzioni per aprire o rimuovere."""
    for doc_id, file_name in document_names.items():
        st.write(f"Documento: {file_name}")
        if st.button(f"Apri {file_name}", key=f"open_{doc_id}"):
            open_document(file_name)
        if st.button(f"Rimuovi {file_name}", key=f"remove_{doc_id}"):
            delete_document(vector_store, doc_id)
            del st.session_state.document_names[doc_id]
            st.success(f"Documento '{file_name}' rimosso con successo!")

def open_document(file_name):
    """Apre il documento con l'applicazione di default."""
    file_path = os.path.join("data", file_name)
    if os.path.exists(file_path):
        if os.name == "posix":
            subprocess.call(["open" if os.uname().sysname == "Darwin" else "xdg-open", file_path])
        elif os.name == "nt":
            os.startfile(file_path)
    else:
        st.error(f"Il file {file_name} non è stato trovato.")

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
