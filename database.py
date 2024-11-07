# database.py
import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

BASE_KB_PATH = "knowledge_bases"  # Directory principale per le knowledge base


def load_or_create_chroma_db(kb_name="default_kb"):
    """Carica o crea una knowledge base specifica usando Chroma."""
    try:
        # Percorso specifico per la knowledge base
        kb_path = os.path.join(BASE_KB_PATH, kb_name)
        os.makedirs(kb_path, exist_ok=True)  # Crea la directory se non esiste

        # Configura la funzione di embedding e carica o crea la knowledge base
        embedding_function = OpenAIEmbeddings()
        vector_store = Chroma(persist_directory=kb_path, embedding_function=embedding_function)

        return vector_store
    except Exception as e:
        print(f"Errore durante il caricamento della knowledge base '{kb_name}': {e}")
        return None  # Ritorna None in caso di errore
