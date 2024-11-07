import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime
from utils.embeddings import create_embeddings
from utils.document_loader import load_document, split_text
import database
class DocumentManager:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

    def __init__(self, kb_name=None):
        """Inizializza il DocumentManager per una knowledge base specifica."""
        self.kb_name = kb_name or "default_kb"
        self.vector_store = database.load_or_create_chroma_db(self.kb_name)
        self.init_session_state()  # Assicurati che session_state sia inizializzato

    def init_session_state(self):
        """Inizializza variabili nel session state."""
        if "document_names" not in st.session_state:
            st.session_state["document_names"] = {}
        if f"loaded_documents_{self.kb_name}" not in st.session_state:
            st.session_state[f"loaded_documents_{self.kb_name}"] = False
        if "refresh_counter" not in st.session_state:
            st.session_state["refresh_counter"] = 0
    def calculate_file_hash(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def document_exists(self, file_hash):
        results = self.vector_store._collection.get(include=["metadatas"])
        return any(metadata.get("file_hash") == file_hash for metadata in results["metadatas"])

    def add_document(self, file_path, chunk_size=500, chunk_overlap=50):
        """Aggiunge un documento, suddividendolo in chunk e salvandolo nella KB."""
        if "document_names" not in st.session_state:
            st.session_state["document_names"] = {}  # Inizializzazione di sicurezza

        """Aggiunge un documento alla KB."""
        file_name = os.path.basename(file_path)
        file_hash = self.calculate_file_hash(file_path)
        abs_file_path = os.path.abspath(file_path)

        if self.document_exists(file_hash):
            st.warning(f"Il documento '{file_name}' è già presente nella KB '{self.kb_name}'.")
            return

        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(file_path) / 1024
        creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = load_document(file_path)
        chunks = split_text(data, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

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

        # Aggiungi i documenti alla knowledge base
        self.vector_store.add_documents(chunks)
        self.vector_store.persist()

        st.session_state.document_names[doc_id] = {
            "file_name": file_name,
            "file_hash": file_hash,
            "file_path": abs_file_path
        }
        st.success(f"Documento '{file_name}' aggiunto alla KB '{self.kb_name}' con successo!")
    def load_existing_documents(self):
        """Carica documenti esistenti per evitare duplicati."""
        if self.vector_store and not st.session_state.get(f"loaded_documents_{self.kb_name}", False):
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
            st.session_state[f"loaded_documents_{self.kb_name}"] = True

    def delete_document(self, doc_id):
        """Elimina un documento dalla KB selezionata."""
        try:
            if doc_id in st.session_state.document_names:
                self.vector_store._collection.delete(ids=[doc_id])
                self.vector_store.persist()
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
        """Apre il documento dal percorso memorizzato in `session_state`."""
        if doc_id in st.session_state.document_names:
            file_path = st.session_state.document_names[doc_id]["file_path"]
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                st.error("Il file non è stato trovato al percorso specificato.")
        else:
            st.error("Documento non trovato in `session_state`.")

    def add_folder(self, folder_path, chunk_size, chunk_overlap):
        """Carica tutti i file supportati dalla cartella selezionata nella KB."""
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    self.add_document(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                else:
                    st.warning(f"Il file '{file}' è stato scartato perché non supportato.")
