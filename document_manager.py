import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime
from utils.embeddings import create_embeddings
from utils.document_loader import load_document, split_text  # Per gestione documenti e chunk

class DocumentManager:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.init_session_state()

    def init_session_state(self):
        """Inizializza variabili nel session state."""
        if "document_names" not in st.session_state:
            st.session_state["document_names"] = {}
        if "loaded_documents" not in st.session_state:
            st.session_state["loaded_documents"] = False
        if "refresh_counter" not in st.session_state:
            st.session_state["refresh_counter"] = 0

    def calculate_file_hash(self, file_path):
        """Calcola un hash univoco per il file per identificare duplicati basati sul contenuto."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def document_exists(self, file_hash):
        """Controlla se un documento con lo stesso hash è già presente nel database."""
        results = self.vector_store._collection.get(include=["metadatas"])
        for metadata in results["metadatas"]:
            if metadata.get("file_hash") == file_hash:
                return True
        return False

    def add_document(self, file_path, chunk_size=500, chunk_overlap=50):
        """Carica e aggiunge un documento, suddividendolo in chunk e salvandolo nel database."""
        file_name = os.path.basename(file_path)
        file_hash = self.calculate_file_hash(file_path)
        abs_file_path = os.path.abspath(file_path)

        # Verifica duplicati
        if self.document_exists(file_hash):
            st.warning(f"Il documento '{file_name}' è già presente nel database.")
            return

        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(file_path) / 1024
        creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Carica e divide il contenuto del documento in chunk personalizzati
        data = load_document(file_path)
        chunks = split_text(data, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Aggiungi ogni chunk al database con i metadati del documento
        for chunk in chunks:
            chunk.metadata.update({
                "doc_id": doc_id,
                "file_name": file_name,
                "file_size": file_size,
                "creation_date": creation_date,
                "upload_date": upload_date,
                "file_hash": file_hash,
                "file_path": abs_file_path
            })

        # Aggiungi i chunk al database
        if self.vector_store is None:
            self.vector_store = create_embeddings(chunks)
        else:
            self.vector_store.add_documents(chunks)
        self.vector_store.persist()

        # Aggiorna `session_state`
        st.session_state.document_names[doc_id] = {
            "file_name": file_name,
            "file_hash": file_hash,
            "file_path": abs_file_path
        }
        st.success(f"Documento '{file_name}' aggiunto alla knowledge base con successo!")

    def load_existing_documents(self):
        """Carica i documenti esistenti dal database e li memorizza in `session_state` per evitare duplicati."""
        if self.vector_store and not st.session_state.get("loaded_documents", False):
            results = self.vector_store._collection.get(include=["metadatas"])
            for metadata in results["metadatas"]:
                doc_id = metadata.get("doc_id")
                file_name = metadata.get("file_name", "Senza Nome")
                file_hash = metadata.get("file_hash")
                file_path = metadata.get("file_path")

                if doc_id and file_name and doc_id not in st.session_state.document_names:
                    st.session_state.document_names[doc_id] = {
                        "file_name": file_name,
                        "file_hash": file_hash,
                        "file_path": file_path
                    }
            st.session_state.loaded_documents = True

    def delete_document(self, doc_id):
        """Elimina un documento dal database usando il suo ID."""
        try:
            if doc_id in st.session_state.document_names:
                self.vector_store._collection.delete(ids=[doc_id])
                self.vector_store.persist()

                # Verifica l'eliminazione
                exists = self.vector_store._collection.get(ids=[doc_id])
                if exists:
                    st.warning(f"Il documento con ID '{doc_id}' non è stato eliminato correttamente.")
                else:
                    del st.session_state.document_names[doc_id]
                    st.success(f"Documento con ID '{doc_id}' rimosso con successo.")
        except Exception as e:
            st.error(f"Errore durante l'eliminazione del documento: {e}")

    def get_document_metadata(self):
        """Recupera i metadati dei documenti per la visualizzazione nella tabella."""
        if not self.vector_store:
            return []

        results = self.vector_store._collection.get(include=["metadatas"])
        documents = []
        seen_hashes = set()

        for metadata in results["metadatas"]:
            file_hash = metadata.get("file_hash")
            if file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                documents.append({
                    "ID Documento": metadata.get("doc_id"),
                    "Nome Documento": metadata.get("file_name", "Senza Nome"),
                    "Dimensione (KB)": f"{metadata.get('file_size', 0):.2f} KB",
                    "Data Creazione": metadata.get("creation_date", "N/A"),
                    "Data Caricamento": metadata.get("upload_date", "N/A"),
                    "Percorso Assoluto": metadata.get("file_path")
                })
        return documents

    def open_document(self, doc_id):
        """Apre il documento usando il percorso assoluto memorizzato in `session_state`."""
        if doc_id in st.session_state.document_names:
            file_path = st.session_state.document_names[doc_id]["file_path"]
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                st.error("Il file non è stato trovato al percorso specificato.")
        else:
            st.error("Documento non trovato in `session_state`.")

    def add_folder(self, folder_path, chunk_size, chunk_overlap):
        """Carica ricorsivamente tutti i file accettati dalla cartella specificata."""
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    # Passa chunk_size e chunk_overlap al metodo add_document
                    self.add_document(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                else:
                    st.warning(f"Il file '{file}' è stato scartato perché non supportato.")