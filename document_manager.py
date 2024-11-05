import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime
from utils.embeddings import create_embeddings

def calculate_file_hash(file_path):
    """Calcola un hash univoco per il file per identificare duplicati basati sul contenuto."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_existing_documents(vector_store):
    """Carica i documenti esistenti dal database e li memorizza in `session_state` per evitare duplicati."""
    if vector_store and not st.session_state.get("loaded_documents", False):
        results = vector_store._collection.get(include=["metadatas"])
        for metadata in results["metadatas"]:
            doc_id = metadata.get("doc_id")
            file_name = metadata.get("file_name", "Senza Nome")
            file_hash = metadata.get("file_hash")
            if doc_id and file_name and doc_id not in st.session_state.document_names:
                st.session_state.document_names[doc_id] = {"file_name": file_name, "file_hash": file_hash}
        st.session_state.loaded_documents = True

def document_exists(vector_store, file_hash):
    """Controlla se un documento con lo stesso hash è già presente nel database."""
    results = vector_store._collection.get(include=["metadatas"])
    for metadata in results["metadatas"]:
        if metadata.get("file_hash") == file_hash:
            return True
    return False

def add_document_to_db(vector_store, chunks, file_path):
    """Aggiunge un documento e i suoi chunk al database e aggiorna `session_state` evitando duplicati tramite hash."""
    file_name = os.path.basename(file_path)
    file_hash = calculate_file_hash(file_path)  # Calcola l'hash per il controllo duplicati

    # Verifica duplicati prima dell'aggiunta
    if document_exists(vector_store, file_hash):
        st.warning(f"Il documento '{file_name}' è già presente nel database.")
        return  # Interrompe l'aggiunta in caso di duplicato

    # Crea metadati per il nuovo documento
    doc_id = str(uuid.uuid4())
    file_size = os.path.getsize(file_path) / 1024  # Converti dimensione in KB
    creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Aggiunge i metadati a ciascun chunk
    for chunk in chunks:
        chunk.metadata.update({
            "doc_id": doc_id,
            "file_name": file_name,
            "file_size": file_size,
            "creation_date": creation_date,
            "upload_date": upload_date,
            "file_hash": file_hash
        })

    # Aggiungi al database e salva
    if vector_store is None:
        vector_store = create_embeddings(chunks)
    else:
        vector_store.add_documents(chunks)
    vector_store.persist()

    # Aggiorna `session_state` con il nuovo documento
    st.session_state.document_names[doc_id] = {"file_name": file_name, "file_hash": file_hash}
    st.success(f"Documento '{file_name}' aggiunto alla knowledge base con successo!")
def delete_document(vector_store, doc_id):
    try:
        if doc_id in st.session_state.document_names:
            vector_store._collection.delete(ids=[doc_id])
            vector_store.persist()

            # Verifica che il documento sia stato effettivamente eliminato
            exists = vector_store._collection.get(ids=[doc_id])
            if exists:
                st.warning(f"Il documento con ID '{doc_id}' non è stato eliminato correttamente.")
            else:
                del st.session_state.document_names[doc_id]
                st.success(f"Documento con ID '{doc_id}' rimosso con successo.")
    except Exception as e:
        st.error(f"Errore durante l'eliminazione del documento: {e}")


def get_document_metadata(vector_store):
    """Recupera i metadati dei documenti dal database per la visualizzazione nella tabella."""
    if not vector_store:
        return []

    results = vector_store._collection.get(include=["metadatas"])
    documents = []
    seen_hashes = set()  # Set per evitare duplicati basati sull'hash

    for metadata in results["metadatas"]:
        file_hash = metadata.get("file_hash")
        if file_hash not in seen_hashes:
            seen_hashes.add(file_hash)  # Aggiungi l'hash per evitare duplicati
            documents.append({
                "ID Documento": metadata.get("doc_id"),
                "Nome Documento": metadata.get("file_name", "Senza Nome"),
                "Dimensione (KB)": f"{metadata.get('file_size', 0):.2f} KB",
                "Data Creazione": metadata.get("creation_date", "N/A"),
                "Data Caricamento": metadata.get("upload_date", "N/A")
            })
    return documents
