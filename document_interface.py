#document_interface.py

import os
import streamlit as st
from document_manager import DocumentManager
from ui_components import apply_custom_css
from database import load_or_create_chroma_db


class DocumentInterface:
    def __init__(self, vector_store, upload_dir="uploaded_documents"):
        self.vector_store = vector_store
        self.upload_dir_base = upload_dir  # Directory base per gli upload
        self.upload_dir = self.get_upload_dir()  # Directory specifica per la KB
        self.doc_manager = DocumentManager(self.vector_store, self.upload_dir)
        # Crea la directory di upload se non esiste
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def update_vector_store(self, vector_store):
        """Aggiorna il vector store e le directory associate."""
        self.vector_store = vector_store
        self.upload_dir = self.get_upload_dir()
        self.doc_manager.vector_store = self.vector_store
        self.doc_manager.upload_dir = self.upload_dir
        # Crea la directory di upload se non esiste
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    def get_upload_dir(self):
        """Ottiene il percorso della directory di upload per la KB selezionata."""
        kb_name = st.session_state.get("selected_kb", "default")
        return os.path.join(self.upload_dir_base, f"kb_{kb_name}")

    def save_uploaded_files(self, uploaded_files):
        """
        Salva i file caricati tramite `st.file_uploader` nella directory di upload.
        """
        saved_files = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(self.upload_dir, uploaded_file.name)

            # Scrivi il contenuto del file nella directory
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_files.append(file_path)

        return saved_files

    def add_web_document(self, url, chunk_size=1024, chunk_overlap=128, depth_level=1):
        """
        Wrapper per chiamare la funzione `add_web_document` in `DocumentManager`.
        """
        try:
            message = self.doc_manager.add_web_document(
                url,
                chunk_size,
                chunk_overlap,
                depth_level=depth_level  # Passiamo il livello di profondità
            )
            st.success(message)
        except ValueError as ve:
            st.error(f"Errore: {ve}")
        except Exception as e:
            st.error(f"Errore durante l'aggiunta del documento web: {e}")

    def truncate_text(self, text, max_length=30):
        return text if len(text) <= max_length else text[:max_length] + "..."

    def initialize_vector_store(self):
        kb_name = st.session_state.get("selected_kb", "default")
        self.vector_store = load_or_create_chroma_db(kb_name)
        self.doc_manager.vector_store = self.vector_store

    def show(self):
        apply_custom_css()

        # ---- Sezione per la Gestione delle Knowledge Base ----
        # Creazione di una nuova knowledge base
        st.markdown("---")
        st.markdown("### 🆕 Crea una nuova Knowledge Base")
        new_kb_name = st.text_input("Nome della nuova Knowledge Base", value="")
        if st.button("Crea Knowledge Base"):
            if new_kb_name:
                kb_list = st.session_state.get("knowledge_bases", [])
                if new_kb_name not in kb_list:
                    kb_list.append(new_kb_name)
                    st.session_state["knowledge_bases"] = kb_list
                    st.session_state["selected_kb"] = new_kb_name
                    st.success(f"Knowledge Base '{new_kb_name}' creata e selezionata.")
                    # Reinizializza il vector store con la nuova KB
                    self.vector_store = load_or_create_chroma_db(new_kb_name)
                    self.doc_manager.vector_store = self.vector_store
                    # Aggiorna la directory di upload
                    self.upload_dir = self.get_upload_dir()
                    self.doc_manager.upload_dir = self.upload_dir
                    # Crea la directory di upload se non esiste
                    if not os.path.exists(self.upload_dir):
                        os.makedirs(self.upload_dir)
                else:
                    st.warning("Una Knowledge Base con questo nome esiste già.")
            else:
                st.warning("Inserisci un nome per la nuova Knowledge Base.")

        # Inizializza il vector store se non è già stato fatto
        if not hasattr(self, 'vector_store') or self.vector_store is None:
            self.initialize_vector_store()

        # Carica documenti esistenti nel database e aggiorna `session_state`
        self.doc_manager.load_existing_documents()
        documents = self.doc_manager.get_document_metadata()

        # ---- Opzioni per la dimensione dei chunk ----
        with st.container():
            st.markdown("---")
            """st.markdown("### 🧩 Imposta Chunk")

            col1, col2 = st.columns([1, 1])
            with col1:
                chunk_size = st.number_input(
                    "Dimensione Chunk",
                    min_value=100,
                    max_value=2000,
                    value=1024,
                    step=100,
                    help="Dimensione di ogni chunk"
                )
            with col2:
                chunk_overlap = st.number_input(
                    "Sovrapposizione Chunk",
                    min_value=0,
                    max_value=500,
                    value=128,
                    step=10,
                    help="Sovrapposizione dei chunk"
                )
"""
            # ---- Drag-and-Drop per File ----
            #st.markdown("---")
            st.markdown("### 📂 Carica File o Cartelle")

            uploaded_files = st.file_uploader(
                "Trascina qui file o selezionali dal tuo sistema.",
                type=["pdf", "docx", "txt", "doc"],
                accept_multiple_files=True,
                help="Puoi trascinare più file contemporaneamente."
            )

            if uploaded_files:
                saved_files = self.save_uploaded_files(uploaded_files)

                for file_path in saved_files:
                    self.doc_manager.add_document(
                        file_path)
                st.success(f"Caricati {len(saved_files)} documenti con successo!")
            # ---- Input per URL ----
            st.markdown("---")
            st.markdown("### 🌐 Carica Sito Web")
            url_input = st.text_input("Inserisci l'URL del sito web", placeholder="https://esempio.com")

            # Aggiungiamo un campo per il livello di profondità
            depth_level = st.number_input(
                "Livello di profondità",
                min_value=1,
                max_value=5,
                value=1,
                step=1,
                help="Indica fino a quale livello di link scendere"
            )

            if st.button("Carica Sito Web"):
                if url_input:
                    self.add_web_document(
                        url_input,
                       depth_level=depth_level  # Passiamo il livello di profondità
                    )
                else:
                    st.warning("Inserisci un URL valido prima di caricare.")

        # ---- Visualizzazione della Tabella Documenti ----
        if documents:
            st.markdown("---")
            st.markdown("### 📑 Documenti nella Knowledge Base")

            header_cols = st.columns([2, 1.5, 1.5, 1.5, 1, 1, 1])
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

                    # Nome Documento e altre informazioni
                    col1.markdown(
                        f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{doc["Nome Documento"]}</div>',
                        unsafe_allow_html=True
                    )
                    col2.markdown(
                        f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{doc["Tipo"]}</div>',
                        unsafe_allow_html=True
                    )

                    # Colonna Fonte con testo troncato e tooltip
                    fonte_troncata = self.truncate_text(doc["Fonte"], max_length=30)
                    col3.markdown(
                        f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;" title="{doc["Fonte"]}">{fonte_troncata}</div>',
                        unsafe_allow_html=True
                    )

                    # Dimensione e Data Caricamento
                    col4.markdown(
                        f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{doc["Dimensione (KB)"]}</div>',
                        unsafe_allow_html=True
                    )
                    col5.markdown(
                        f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{doc["Data Caricamento"]}</div>',
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
            st.warning("Knowledge base vuoto.")