#document_manager.py

import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime
from utils.processing.embeddings import create_embeddings
from utils.loaders.document_loader import load_document, split_text  # Per gestione documenti e chunk
import validators
from urllib.parse import urljoin
import requests
from langchain.schema import Document  # Se non già importato
from bs4 import BeautifulSoup
class DocumentManager:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".csv"}
    WEB_DOCUMENT_ID_PREFIX = "web_"  # Prefisso per documenti caricati da URL

    def __init__(self, vector_store, upload_dir="uploaded_documents"):
        if vector_store is None:
            vector_store = create_embeddings([])  # Usa una funzione che crea un nuovo vector store
        self.vector_store = vector_store
        self.init_session_state()
        self.table_placeholder = st.empty()

    def init_session_state(self):
        """Inizializza variabili nel session state."""
        kb_key = f"document_names_{self.vector_store._persist_directory}"
        if kb_key not in st.session_state:
            st.session_state[kb_key] = {}
        if "loaded_documents" not in st.session_state:
            st.session_state["loaded_documents"] = {}
        if "refresh_counter" not in st.session_state:
            st.session_state["refresh_counter"] = 0

    def calculate_file_hash(self, file_path):
        """Calcola un hash univoco per il file per identificare duplicati basati sul contenuto."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def document_exists(self, file_hash=None, url=None):
        """Controlla se un documento con lo stesso hash o URL è già presente nel database."""
        if not self.vector_store or not hasattr(self.vector_store, '_collection'):
            return False

        results = self.vector_store._collection.get(include=["metadatas"])
        for metadata in results["metadatas"]:
            if file_hash and metadata.get("file_hash") == file_hash:
                return True
            if url and metadata.get("source_url") == url:
                return True
        return False

    def add_document(self, file_path_or_url, chunk_size=1024, chunk_overlap=128):
        """
        Carica e aggiunge un documento (locale o URL) al vector store.
        """
        if isinstance(file_path_or_url, list):
            for single_path in file_path_or_url:
                self.add_document(single_path, chunk_size, chunk_overlap)
            return

        if validators.url(file_path_or_url):
            self.add_web_document(file_path_or_url, chunk_size, chunk_overlap)
            return

        self.add_local_document(file_path_or_url, chunk_size, chunk_overlap)

    def add_local_document(self, file_path, chunk_size=1024, chunk_overlap=128):
        """
        Carica e aggiunge un documento locale suddividendolo in chunk.
        """
        file_name = os.path.basename(file_path)
        file_hash = self.calculate_file_hash(file_path)
        abs_file_path = os.path.abspath(file_path)

        if self.document_exists(file_hash):
            st.warning(f"Il documento '{file_name}' è già presente nella knowledge base.")
            return

        try:
            data = load_document(file_path)
            if not data:
                st.error(f"Errore: Impossibile caricare il documento '{file_name}'.")
                return

            chunks = split_text(data, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            if not chunks:
                st.error(f"Errore: Il documento '{file_name}' non può essere suddiviso in chunk.")
                return

            doc_id = str(uuid.uuid4())
            for chunk in chunks:
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "file_size": os.path.getsize(file_path) / 1024,
                    "creation_date": datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
                    "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file_hash": file_hash,
                    "file_path": abs_file_path,
                })

            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            st.session_state["refresh_counter"] += 1
            st.success(f"Documento '{file_name}' aggiunto con successo!")
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del documento '{file_name}': {e}")

    def fetch_web_content(self, url, depth_level=1, visited=None, max_pages=50):
        """Scarica e analizza il contenuto di una pagina web fino al livello di profondità specificato."""
        if visited is None:
            visited = set()
        if depth_level < 1 or len(visited) >= max_pages:
            return []

        # Controlla se l'URL è già stato visitato per prevenire loop
        if url in visited:
            return []
        visited.add(url)

        try:
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0"
            })

            if "text/html" not in response.headers.get("Content-Type", ""):
                return []

            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Estrarre solo il testo visibile
            text = soup.get_text(separator="\n", strip=True)
            documents = [{"url": url, "content": text}]

            if depth_level > 1:
                # Trova tutti i link nella pagina
                links = [a.get('href') for a in soup.find_all('a', href=True)]
                # Processa i link per ottenere URL assoluti
                links = [urljoin(url, link) if not link.startswith('http') else link for link in links]
                # Filtra link non validi
                links = [
                    link for link in links
                    if not link.startswith('mailto:')
                       and not link.startswith('javascript:')
                       and link not in visited
                ]

                # Scarica il contenuto dei link ricorsivamente
                for link in links:
                    if len(visited) >= max_pages:
                        break
                    documents.extend(
                        self.fetch_web_content(
                            link,
                            depth_level=depth_level - 1,
                            visited=visited,
                            max_pages=max_pages
                        )
                    )

            return documents
        except Exception as e:
            return []

    def add_web_document(self, url, chunk_size=1024, chunk_overlap=128, depth_level=1):
        """
        Scarica il contenuto di un sito web, lo divide in chunk e lo aggiunge alla knowledge base.
        """
        if not validators.url(url):
            st.error("URL non valido. Inserisci un URL corretto.")
            return

        # Scaricare il contenuto web usando fetch_web_content
        web_documents = self.fetch_web_content(url, depth_level=depth_level)

        if not web_documents:
            st.error(f"Errore: Nessun contenuto trovato per l'URL: {url}")
            return

        doc_id = str(uuid.uuid4())
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for web_doc in web_documents:
            page_content = web_doc['content']
            page_url = web_doc['url']
            # Creiamo un oggetto Document per ogni pagina
            document = Document(page_content=page_content, metadata={"source_url": page_url})
            # Suddividiamo il documento in chunk
            chunks = split_text([document], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            if not chunks:
                continue  # Salta se non ci sono chunk

            for chunk in chunks:
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "file_name": "Contenuto Web",
                    "file_size": len(chunk.page_content) / 1024,  # Dimensione in KB
                    "creation_date": "N/A",
                    "upload_date": upload_date,
                    "source_url": page_url,
                })

            try:
                self.vector_store.add_documents(chunks)
            except Exception as e:
                st.error(f"Errore durante l'aggiunta del documento web: {e}")

        self.vector_store.persist()
        st.success(f"Contenuto da '{url}' aggiunto con successo!")
        st.session_state["refresh_counter"] += 1

    def load_existing_documents(self):
        """Carica i documenti esistenti dal database e li memorizza in `session_state` per evitare duplicati."""
        kb_key = f"document_names_{self.vector_store._persist_directory}"
        if self.vector_store and not st.session_state.get(f"loaded_documents_{self.vector_store._persist_directory}",
                                                          False):
            if kb_key not in st.session_state:
                st.session_state[kb_key] = {}
            results = self.vector_store._collection.get(include=["metadatas"])
            for metadata in results["metadatas"]:
                doc_id = metadata.get("doc_id")
                file_name = metadata.get("file_name", "Senza Nome")
                file_hash = metadata.get("file_hash")
                file_path = metadata.get("file_path")

                if doc_id and file_name and doc_id not in st.session_state[kb_key]:
                    st.session_state[kb_key][doc_id] = {
                        "file_name": file_name,
                        "file_hash": file_hash,
                        "file_path": file_path
                    }
            st.session_state[f"loaded_documents_{self.vector_store._persist_directory}"] = True

    def truncate_text(self, text, max_length=50):
        """
        Trunca un testo se supera la lunghezza massima specificata.
        Aggiunge '...' alla fine per indicare il troncamento.

        Parameters:
        - text (str): Il testo da troncate.
        - max_length (int): La lunghezza massima.

        Returns:
        - str: Il testo troncato.
        """
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def show_documents(self):
        """Visualizza la tabella dei documenti nella knowledge base."""
        # Inizializza il refresh_counter se non esiste
        if "refresh_counter" not in st.session_state:
            st.session_state["refresh_counter"] = 0

        # Utilizza il refresh_counter per aggiornare la tabella
        refresh_counter = st.session_state["refresh_counter"]

        self.load_existing_documents()
        documents = self.get_document_metadata()
        with self.table_placeholder:
            # ---- Visualizzazione della Tabella Documenti ----
            if documents:
                st.markdown("---")
                st.markdown("### 📑 Documenti nella Knowledge Base")

                header_cols = st.columns([2, 1.5, 2, 1.5, 1.5, 1, 1])
                headers = ["Nome Documento", "Tipo", "Fonte", "Dimensione (KB)", "Data Caricamento", "Elimina",
                           "Apri Risorsa"]
                for header, col in zip(headers, header_cols):
                    col.markdown(f"**{header}**")

                row_colors = ["#2a2a2a", "#3d3d3d"]
                text_color = "#e0e0e0"

                for idx, doc in enumerate(documents):
                    row_color = row_colors[idx % 2]
                    with st.container():
                        # Allinea le colonne con proporzioni corrette
                        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 2, 1.5, 1.5, 1, 1])

                        # Inserisce i dati nelle colonne, usando truncate_text per gestire i testi lunghi
                        for col, text in zip(
                                [col1, col2, col3, col4, col5],
                                [
                                    self.truncate_text(doc["Nome Documento"]),
                                    self.truncate_text(doc["Tipo"]),
                                    self.truncate_text(doc["Fonte"], max_length=30),
                                    doc["Dimensione (KB)"],
                                    doc["Data Caricamento"]
                                ]
                        ):
                            col.markdown(
                                f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{text}</div>',
                                unsafe_allow_html=True
                            )

                        # Pulsante "Elimina"
                        if col6.button("Elimina", key=f"delete_{doc['ID Documento']}"):
                            self.doc_manager.delete_document(doc["ID Documento"])

                        # Pulsante "Apri Risorsa"
                        if col7.button("Apri Risorsa", key=f"open_{doc['ID Documento']}"):
                            if doc["Tipo"] == "Web":
                                st.info(f"Apertura URL: {doc['Fonte']}")
                                st.markdown(f"[Apri in una nuova scheda]({doc['Fonte']})", unsafe_allow_html=True)
                            else:
                                self.doc_manager.open_document(doc["ID Documento"])

            else:
                st.info("Nessun documento presente nella knowledge base.")

    def delete_document(self, doc_id):
        """Elimina un documento dal database e dal vector store usando il suo ID."""
        kb_key = f"document_names_{self.vector_store._persist_directory}"
        try:
            if doc_id in st.session_state.get(kb_key, {}):
                # Elimina tutti i vettori associati al documento tramite il filtro sul metadato 'doc_id'
                self.vector_store._collection.delete(where={"doc_id": doc_id})
                self.vector_store.persist()

                # Verifica l'eliminazione
                exists = self.vector_store._collection.get(
                    where={"doc_id": doc_id},
                    include=["metadatas"]
                )
                if exists['metadatas']:
                    st.warning(f"Il documento con ID '{doc_id}' non è stato eliminato correttamente.")
                else:
                    del st.session_state[kb_key][doc_id]
                    st.success(f"Documento con ID '{doc_id}' rimosso con successo.")

                    # Aggiorna il session_state per forzare l'aggiornamento della tabella
                    st.session_state["refresh_counter"] += 1
            else:
                st.warning(f"Il documento con ID '{doc_id}' non è presente nella knowledge base.")
        except Exception as e:
            st.error(f"Errore durante l'eliminazione del documento: {e}")

    def get_document_metadata(self):
        """Recupera i metadati dei documenti per la visualizzazione nella knowledge base."""
        if not self.vector_store:
            return []

        kb_key = f"document_names_{self.vector_store._persist_directory}"
        if kb_key not in st.session_state:
            st.session_state[kb_key] = {}

        results = self.vector_store._collection.get(include=["metadatas"])
        documents = []
        seen_doc_ids = set()

        for metadata in results["metadatas"]:
            doc_id = metadata.get("doc_id")
            if doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                fonte = metadata.get("source_url", metadata.get("file_path", "N/A"))

                # Rendi la colonna "Fonte" cliccabile se è un URL
                if validators.url(fonte):
                    fonte = f"[Apri URL]({fonte})"

                documents.append({
                    "ID Documento": doc_id,
                    "Nome Documento": metadata.get("file_name", "Senza Nome"),
                    "Tipo": "Web" if metadata.get("source_url") else "File",
                    "Fonte": fonte,
                    "Dimensione (KB)": f"{metadata.get('file_size', 0):.2f}",
                    "Data Caricamento": metadata.get("upload_date", "N/A"),
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
