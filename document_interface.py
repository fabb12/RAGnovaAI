import streamlit as st
from tkinter import Tk, filedialog
from document_manager import DocumentManager
from ui_components import apply_custom_css


class DocumentInterface:
    def __init__(self, vector_store):
        self.doc_manager = DocumentManager(vector_store)

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

        # Carica documenti esistenti nel database e aggiorna `session_state`
        self.doc_manager.load_existing_documents()
        documents = self.doc_manager.get_document_metadata()

        # ---- Opzioni per la dimensione dei chunk e selezione file/cartella ----
        with st.container():
            st.markdown("---")  # Linea di separazione visiva
            st.markdown("### 🧩 Imposta Chunk")

            # Prima riga: campi per impostare `chunk_size` e `chunk_overlap`
            col1, col2 = st.columns([1, 1])
            with col1:
                chunk_size = st.number_input("Dimensione Chunk", min_value=100, max_value=2000, value=500, step=100,
                                             help="Dimensione di ogni chunk")
            with col2:
                chunk_overlap = st.number_input("Sovrapposizione Chunk", min_value=0, max_value=500, value=50, step=10,
                                                help="Sovrapposizione dei chunk")

            st.markdown("---")  # Linea di separazione visiva
            st.markdown("### 📂 Carica Documenti")
            # Seconda riga: bottoni per "Seleziona Cartella" e "Seleziona File"
            col3, col4 = st.columns([1, 1])
            with col3:
                if st.button("Seleziona Cartella"):
                    folder_path = self.select_folder()
                    if folder_path:
                        self.doc_manager.add_folder(folder_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        st.success(f"Documenti dalla cartella '{folder_path}' caricati con successo!")

            with col4:
                if st.button("Seleziona File"):
                    file_paths = self.select_files()
                    if file_paths:
                        for file_path in file_paths:
                            self.doc_manager.add_document(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        st.success(f"Caricati {len(file_paths)} documenti con successo!")

        # ---- Visualizzazione della Tabella Documenti ----
        if documents:
            st.markdown("---")  # Linea di separazione
            st.markdown("### 📑 Documenti nella Knowledge Base")

            # Intestazioni delle colonne della tabella
            header_cols = st.columns([2, 1.5, 1.5, 1.5, 1, 1])
            headers = ["Nome Documento", "Dimensione (KB)", "Data Creazione", "Data Caricamento", "Azione", "Apri"]
            for header, col in zip(headers, header_cols):
                col.markdown(f"**{header}**")

            # Colori scuri alternati per righe e testo chiaro
            row_colors = ["#2a2a2a", "#3d3d3d"]  # Colori scuri alternati
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
                        st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo!")

                    if col6.button("Apri", key=f"open_{doc_id}"):
                        self.doc_manager.open_document(doc_id)

        # Forza un refresh della pagina per aggiornare la lista dei documenti
        st.experimental_rerun() if st.session_state.get("refresh_counter") else None
