# manage_documents.py

import streamlit as st
import os
import subprocess
from utils.document_loader import load_document, split_text
from document_manager import load_existing_documents, add_document_to_db, get_document_metadata, delete_document
from ui_components import apply_custom_css
from datetime import datetime

LOCAL_DATA_PATH = "data"


def show_manage_documents_page(vector_store):
    """Mostra l'interfaccia di gestione documenti per aggiungere, visualizzare, aprire ed eliminare documenti dal database."""

    apply_custom_css()
    st.header("Gestione Documenti")

    # Inizializza `session_state` per i nomi dei documenti
    if "document_names" not in st.session_state:
        st.session_state.document_names = {}
    load_existing_documents(vector_store)

    # ---- Sezione per Caricare Nuovi Documenti dal Computer ----
    st.subheader("Aggiungi Nuovi Documenti")

    # Opzione 1: Caricamento multiplo di file
    uploaded_files = st.file_uploader(
        "Carica uno o più file PDF, DOCX o TXT",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = f"{LOCAL_DATA_PATH}/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            data = load_document(file_path)
            chunk_size = st.number_input("Dimensione chunk:", min_value=100, max_value=2048, value=512)
            chunks = split_text(data, chunk_size=chunk_size)

            add_document_to_db(vector_store, chunks, file_path)
        st.success(f"Caricati {len(uploaded_files)} documenti con successo!")

    # Opzione 2: Caricamento di una cartella
    st.write("### Oppure seleziona una cartella per importare tutti i documenti")
    folder_path = st.text_input("Percorso della cartella contenente i documenti:")
    if st.button("Carica Cartella"):
        if os.path.isdir(folder_path):
            supported_formats = (".pdf", ".docx", ".txt")
            folder_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith(supported_formats)
            ]
            if not folder_files:
                st.warning("Nessun file supportato trovato nella cartella selezionata.")
            else:
                for file_path in folder_files:
                    data = load_document(file_path)
                    chunk_size = st.number_input("Dimensione chunk:", min_value=100, max_value=2048, value=512)
                    chunks = split_text(data, chunk_size=chunk_size)

                    add_document_to_db(vector_store, chunks, file_path)
                st.success(f"Caricati {len(folder_files)} documenti dalla cartella con successo!")
        else:
            st.error("Percorso della cartella non valido.")

    # ---- Sezione per Visualizzare i Documenti Esistenti ----
    st.subheader("Documenti nella Knowledge Base")

    documents = get_document_metadata(vector_store)

    # Intestazioni della tabella
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
    col1.write("Nome Documento")
    col2.write("Dimensione (KB)")
    col3.write("Data Creazione")
    col4.write("Data Caricamento")
    col5.write("Azione")
    col6.write("Apri")

    # Visualizza ogni documento come una riga nella tabella con pulsanti di eliminazione e apertura
    for doc in documents:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
        col1.write(doc["Nome Documento"])
        col2.write(doc["Dimensione (KB)"])
        col3.write(doc["Data Creazione"])
        col4.write(doc["Data Caricamento"])

        unique_delete_key = f"delete_{doc['ID Documento']}"
        if col5.button("Elimina", key=unique_delete_key):
            delete_document(vector_store, doc["ID Documento"])
            del st.session_state.document_names[doc["ID Documento"]]
            st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo!")
            st.experimental_rerun()

        # Pulsante per aprire il file con l'applicazione predefinita
        file_path = os.path.join(LOCAL_DATA_PATH, doc["Nome Documento"])
        unique_open_key = f"open_{doc['ID Documento']}"
        if col6.button("Apri", key=unique_open_key):
            if os.path.exists(file_path):
                if os.name == 'posix':  # Per macOS e Linux
                    subprocess.call(["open" if os.uname().sysname == "Darwin" else "xdg-open", file_path])
                elif os.name == 'nt':  # Per Windows
                    os.startfile(file_path)
            else:
                st.error(f"Il file {doc['Nome Documento']} non è stato trovato.")
