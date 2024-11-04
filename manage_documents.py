# manage_documents.py

import streamlit as st
from database import load_or_create_chroma_db
from utils.document_loader import load_document, split_text
from document_manager import load_existing_documents, add_document_to_db, get_document_metadata, delete_document
from ui_components import apply_custom_css
import os
from datetime import datetime

apply_custom_css()

# Carica o crea il database
vector_store = load_or_create_chroma_db()

st.header("Gestione Documenti")

# Inizializza `session_state` per i nomi dei documenti
if "document_names" not in st.session_state:
    st.session_state.document_names = {}
load_existing_documents(vector_store)

# Aggiungi nuovi documenti
st.subheader("Aggiungi un Nuovo Documento")
uploaded_file = st.file_uploader("Carica un file PDF, DOCX o TXT", type=["pdf", "docx", "txt"])
if uploaded_file:
    # Salva il file caricato e processa i chunk
    file_path = f"data/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    data = load_document(file_path)
    chunk_size = st.number_input("Dimensione chunk:", min_value=100, max_value=2048, value=512)
    chunks = split_text(data, chunk_size=chunk_size)
    add_document_to_db(vector_store, chunks, file_path)

    st.success(f"Documento '{uploaded_file.name}' aggiunto con successo!")

# Tabella dei documenti
st.subheader("Documenti nella Knowledge Base")

# Ottieni i metadati dei documenti
documents = get_document_metadata(vector_store)

# Visualizza l'intestazione della tabella
st.write("### Documenti Caricati")
st.write("Questi sono i documenti attualmente nella knowledge base:")

# Intestazioni della tabella
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
col1.write("Nome Documento")
col2.write("Dimensione (KB)")
col3.write("Data Creazione")
col4.write("Data Caricamento")
col5.write("Azione")

# Visualizza ogni documento come una riga con un pulsante di eliminazione
for doc in documents:
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
    col1.write(doc["Nome Documento"])
    col2.write(doc["Dimensione (KB)"])
    col3.write(doc["Data Creazione"])
    col4.write(doc["Data Caricamento"])

    # Pulsante per eliminare il documento, con `key` univoco
    unique_key = f"delete_{doc['ID Documento']}"
    if col5.button("Elimina", key=unique_key):
        delete_document(vector_store, doc["ID Documento"])
        st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo!")
        st.experimental_rerun()  # Aggiorna la pagina dopo l'eliminazione
