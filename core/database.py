# database.py
from langchain.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
CHROMA_PATH = "chroma"

def load_or_create_chroma_db(kb_name):
    """Carica o crea una knowledge base usando Chroma."""

    # kb_name dovrebbe essere già nel formato username_kbname
    CHROMA_PATH = f"chroma_{kb_name}"
    embedding_function = OpenAIEmbeddings()
    try:
        vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        return vector_store
    except Exception as e:
        print(f"Errore durante il caricamento della knowledge base '{kb_name}': {e}")
        return None
