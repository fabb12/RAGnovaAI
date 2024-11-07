import streamlit as st
from tkinter import Tk, filedialog
from document_manager import DocumentManager
from ui_components import apply_custom_css
from database import load_or_create_chroma_db


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
        st.header("Gestione Documenti")

        self.doc_manager.load_existing_documents()
        documents = self.doc_manager.get_document_metadata()

        st.subheader("Aggiungi Nuovi Documenti")
        if st.button("Seleziona File"):
            file_paths = self.select_files()
            if file_paths:
                for file_path in file_paths:
                    self.doc_manager.add_document(file_path)
                st.session_state["refresh_counter"] += 1
                st.success(f"Caricati {len(file_paths)} documenti con successo!")

        if st.button("Seleziona Cartella"):
            folder_path = self.select_folder()
            if folder_path:
                self.doc_manager.add_folder(folder_path)
                st.success(f"Documenti dalla cartella '{folder_path}' caricati con successo!")

        # Visualizza documenti caricati
        if documents:
            st.subheader("Documenti nella Knowledge Base")
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

                doc_id = doc["ID Documento"]
                if col5.button("Elimina", key=f"delete_{doc_id}"):
                    self.doc_manager.delete_document(doc_id)
                    st.session_state["refresh_counter"] += 1
                    st.success(f"Documento '{doc['Nome Documento']}' rimosso con successo!")

                if col6.button("Apri", key=f"open_{doc_id}"):
                    self.doc_manager.open_document(doc_id)

        st._set_query_params(refresh=st.session_state["refresh_counter"])
