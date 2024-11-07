import streamlit as st
from tkinter import Tk, filedialog
from document_manager import DocumentManager
from ui_components import apply_custom_css
from database import load_or_create_chroma_db
import os

class DocumentInterface:
    def __init__(self, kb_name="default_kb"):
        self.kb_name = kb_name
        self.doc_manager = DocumentManager(kb_name=kb_name)

    def init_doc_manager(self, kb_name):
        """Inizializza il DocumentManager per una knowledge base specifica."""
        self.doc_manager = DocumentManager(kb_name)

    def list_existing_kbs(self):
        """Elenca le knowledge base esistenti nella directory."""
        kb_directory = "knowledge_bases"
        os.makedirs(kb_directory, exist_ok=True)  # Crea la cartella se non esiste
        return [name for name in os.listdir(kb_directory) if os.path.isdir(os.path.join(kb_directory, name))]

    def select_files(self):
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_paths = filedialog.askopenfilenames(
            title="Seleziona i file da caricare",
            filetypes=[("Documenti", "*.pdf;*.docx;*.txt;*.doc"), ("Tutti i file", "*.*")]
        )
        root.destroy()
        return file_paths

    def select_folder(self):
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder_path = filedialog.askdirectory(title="Seleziona la cartella da caricare")
        root.destroy()
        return folder_path

    def show(self):
        apply_custom_css()

        # ---- Sezione di Selezione o Creazione della Knowledge Base ----
        st.markdown("### 🔍 Knowledge Base")
        existing_kbs = self.list_existing_kbs()
        col1, col2 = st.columns([2, 1])

        with col1:
            # Selettore per knowledge base esistente
            self.selected_kb = st.selectbox("Seleziona una Knowledge Base", existing_kbs,
                                            help="Scegli una KB esistente.")
        with col2:
            # Creazione di una nuova knowledge base
            new_kb_name = st.text_input("Crea Nuova KB", placeholder="Nome per nuova KB")
            if st.button("Crea KB") and new_kb_name:
                self.selected_kb = new_kb_name
                if new_kb_name not in existing_kbs:
                    self.init_doc_manager(new_kb_name)
                    st.success(f"KB '{new_kb_name}' creata e selezionata con successo!")
                else:
                    st.warning(f"La KB '{new_kb_name}' esiste già. Seleziona un nome univoco.")

        # ---- Configurazione di Chunk ----
        with st.container():
            st.markdown("---")  # Linea di separazione visiva
            st.markdown("### 🧩 Imposta Chunk")

            # Parametri per chunk size e chunk overlap
            col1, col2 = st.columns([1, 1])
            with col1:
                chunk_size = st.number_input("Dimensione Chunk", min_value=100, max_value=2000, value=500, step=100,
                                             help="Definisce la dimensione dei chunk.")
            with col2:
                chunk_overlap = st.number_input("Sovrapposizione Chunk", min_value=0, max_value=500, value=50, step=10,
                                                help="Definisce la sovrapposizione dei chunk.")

        # ---- Caricamento di Documenti ----
        st.markdown("---")
        st.markdown("### 📂 Carica Documenti")
        col3, col4 = st.columns([1, 1])
        with col3:
            # Caricamento tramite cartella
            if st.button("Seleziona Cartella"):
                folder_path = self.select_folder()
                if folder_path:
                    self.doc_manager.add_folder(folder_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    st.success(f"Documenti dalla cartella '{folder_path}' caricati nella KB '{self.selected_kb}'.")

        with col4:
            # Caricamento di file singoli
            if st.button("Seleziona File"):
                file_paths = self.select_files()
                if file_paths:
                    for file_path in file_paths:
                        self.doc_manager.add_document(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    st.success(f"{len(file_paths)} documenti caricati nella KB '{self.selected_kb}'.")

        # ---- Visualizzazione della Tabella Documenti ----
        documents = self.doc_manager.get_document_metadata()
        if documents:
            st.markdown("---")
            st.markdown("### 📑 Documenti nella Knowledge Base")

            # Intestazioni della tabella
            header_cols = st.columns([2, 1.5, 1.5, 1.5, 1, 1])
            headers = ["Nome Documento", "Dimensione (KB)", "Data Creazione", "Data Caricamento", "Azione", "Apri"]
            for header, col in zip(headers, header_cols):
                col.markdown(f"**{header}**")

            # Colori per la tabella e gestione delle righe
            row_colors = ["#2a2a2a", "#3d3d3d"]
            text_color = "#e0e0e0"

            for idx, doc in enumerate(documents):
                row_color = row_colors[idx % 2]
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1.5, 1, 1])

                    for col, text in zip([col1, col2, col3, col4],
                                         [doc["Nome Documento"], doc["Dimensione (KB)"], doc["Data Creazione"],
                                          doc["Data Caricamento"]]):
                        col.markdown(
                            f'<div style="background-color: {row_color}; color: {text_color}; padding: 5px;">{text}</div>',
                            unsafe_allow_html=True)

                    doc_id = doc["ID Documento"]
                    if col5.button("Elimina", key=f"delete_{doc_id}"):
                        self.doc_manager.delete_document(doc_id)
                        st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo.")

                    if col6.button("Apri", key=f"open_{doc_id}"):
                        self.doc_manager.open_document(doc_id)

        # Aggiorna la pagina per visualizzare i cambiamenti
        st.experimental_rerun() if st.session_state.get("refresh_counter") else None
