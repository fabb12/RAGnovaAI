import streamlit as st
import os
import subprocess
from utils.document_loader import load_document, split_text
from document_manager import load_existing_documents, add_document_to_db, get_document_metadata, delete_document
from ui_components import apply_custom_css
from datetime import datetime
from database import load_or_create_chroma_db

# Percorso locale per i documenti caricati
LOCAL_DATA_PATH = "data"


def show_manage_documents_page(vector_store):
    """Mostra l'interfaccia di gestione documenti per aggiungere, visualizzare, aprire ed eliminare documenti dal database."""

    apply_custom_css()
    st.header("Gestione Documenti")

    # Inizializza session_state per document_names e loaded_documents se non esistono
    if "document_names" not in st.session_state:
        st.session_state["document_names"] = {}
    if "loaded_documents" not in st.session_state:
        st.session_state["loaded_documents"] = False
    if "refresh_counter" not in st.session_state:
        st.session_state["refresh_counter"] = 0

    # Verifica se la knowledge base è stata inizializzata
    if vector_store is None:
        st.warning("La knowledge base non è stata inizializzata. Carica i documenti per crearne una nuova.")
        allow_document_upload = True
        documents = []
    else:
        # Carica documenti esistenti
        load_existing_documents(vector_store)
        documents = get_document_metadata(vector_store)
        allow_document_upload = True

    # ---- Sezione per Caricare Nuovi Documenti ----
    if allow_document_upload:
        st.subheader("Aggiungi Nuovi Documenti")
        uploaded_files = st.file_uploader(
            "Carica uno o più file PDF, DOCX o TXT",
            type=["pdf", "docx", "txt", "doc"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(LOCAL_DATA_PATH, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Carica e suddivide il documento in chunk
                data = load_document(file_path)
                chunks = split_text(data)

                # Crea il database se non esiste
                if vector_store is None:
                    vector_store = load_or_create_chroma_db()

                add_document_to_db(vector_store, chunks, file_path)
            st.session_state["refresh_counter"] += 1
            st.success(f"Caricati {len(uploaded_files)} documenti con successo!")

    # ---- Visualizzazione dei Documenti Esistenti ----
    if vector_store and documents:
        st.subheader("Documenti nella Knowledge Base")

        # Intestazioni della tabella
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
        col1.write("Nome Documento")
        col2.write("Dimensione (KB)")
        col3.write("Data Creazione")
        col4.write("Data Caricamento")
        col5.write("Azione")
        col6.write("Apri")

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
                st._set_query_params(refresh=st.session_state["refresh_counter"])

                if "document_names" in st.session_state and doc["ID Documento"] in st.session_state.document_names:
                    del st.session_state.document_names[doc["ID Documento"]]
                st.session_state["refresh_counter"] += 1
                st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo!")

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

    # Forza un refresh simulato aggiungendo un parametro di query
    st._set_query_params(refresh=st.session_state["refresh_counter"])
