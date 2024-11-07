# database.py
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

CHROMA_PATH = "chroma"

def load_or_create_chroma_db():
    """Carica o crea una knowledge base usando Chroma."""
    try:
        embedding_function = OpenAIEmbeddings()
        vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        return vector_store
    except Exception as e:
        print(f"Errore durante il caricamento della knowledge base: {e}")
        return None  # Ritorna None in caso di errore
