# document_manager.py

import streamlit as st
import uuid
import os
from datetime import datetime
from utils.embeddings import create_embeddings, delete_document

def load_existing_documents(vector_store):
    """Carica i documenti esistenti dal database e li memorizza in `session_state`."""
    if vector_store and not st.session_state.get("loaded_documents", False):
        results = vector_store._collection.get(include=["metadatas"])
        for metadata in results["metadatas"]:
            doc_id = metadata.get("doc_id")
            file_name = metadata.get("file_name", "Senza Nome")
            if doc_id and file_name:
                st.session_state.document_names[doc_id] = file_name
        st.session_state.loaded_documents = True

def add_document_to_db(vector_store, chunks, file_path):
    """Aggiunge il documento e i suoi chunk al database e aggiorna `session_state`."""
    doc_id = str(uuid.uuid4())
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)  # Dimensione del file in byte
    creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Aggiungi i metadati a ogni chunk
    for chunk in chunks:
        chunk.metadata["doc_id"] = doc_id
        chunk.metadata["file_name"] = file_name
        chunk.metadata["file_size"] = file_size
        chunk.metadata["creation_date"] = creation_date
        chunk.metadata["upload_date"] = upload_date

    if vector_store is None:
        vector_store = create_embeddings(chunks)
    else:
        vector_store.add_documents(chunks)
    vector_store.persist()

    st.session_state.document_names[doc_id] = file_name
    st.success(f"Documento '{file_name}' aggiunto alla knowledge base con successo!")
# document_manager.py

def get_document_metadata(vector_store):
    """Recupera i metadati dei documenti dal database per la visualizzazione nella tabella."""
    if not vector_store:
        return []

    results = vector_store._collection.get(include=["metadatas"])
    documents = []
    for metadata in results["metadatas"]:
        documents.append({
            "ID Documento": metadata.get("doc_id"),
            "Nome Documento": metadata.get("file_name", "Senza Nome"),
            "Dimensione (KB)": f"{metadata.get('file_size', 0) / 1024:.2f} KB",  # Converti in KB
            "Data Creazione": metadata.get("creation_date", "N/A"),
            "Data Caricamento": metadata.get("upload_date", "N/A")
        })
    return documents
