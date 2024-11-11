import os
import streamlit as st
from document_manager import DocumentManager
from ui_components import apply_custom_css


class DocumentInterface:
    def __init__(self, vector_store, upload_dir="uploaded_documents"):
        self.doc_manager = DocumentManager(vector_store)
        self.upload_dir = upload_dir

        # Crea la directory di upload se non esiste
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

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

    def show(self):
        apply_custom_css()

        # Carica documenti esistenti nel database e aggiorna `session_state`
        self.doc_manager.load_existing_documents()
        documents = self.doc_manager.get_document_metadata()

        # ---- Opzioni per la dimensione dei chunk ----
        with st.container():
            st.markdown("---")
            st.markdown("### 🧩 Imposta Chunk")

            col1, col2 = st.columns([1, 1])
            with col1:
                chunk_size = st.number_input(
                    "Dimensione Chunk",
                    min_value=100,
                    max_value=2000,
                    value=500,
                    step=100,
                    help="Dimensione di ogni chunk"
                )
            with col2:
                chunk_overlap = st.number_input(
                    "Sovrapposizione Chunk",
                    min_value=0,
                    max_value=500,
                    value=50,
                    step=10,
                    help="Sovrapposizione dei chunk"
                )

            # ---- Drag-and-Drop per File ----
            st.markdown("---")
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
                        file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                    )
                st.success(f"Caricati {len(saved_files)} documenti con successo!")

        # ---- Visualizzazione della Tabella Documenti ----
        if documents:
            st.markdown("---")
            st.markdown("### 📑 Documenti nella Knowledge Base")

            header_cols = st.columns([2, 1.5, 1.5, 1.5, 1, 1])
            headers = ["Nome Documento", "Dimensione (KB)", "Data Creazione", "Data Caricamento", "Azione", "Apri"]
            for header, col in zip(headers, header_cols):
                col.markdown(f"**{header}**")

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

                    if col6.button("Apri", key=f"open_{doc_id}"):
                        self.doc_manager.open_document(doc_id)
