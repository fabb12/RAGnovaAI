# utils/embeddings.py
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os


def create_embeddings(chunks, kb_path):
    """Crea embeddings per i chunk e li salva nel database ChromaDB, anche se è vuoto."""
    os.makedirs(kb_path, exist_ok=True)  # Crea la directory se non esiste

    # Inizializza un database Chroma vuoto se `chunks` è vuoto
    db = Chroma(persist_directory=kb_path, embedding_function=OpenAIEmbeddings())

    # Solo se ci sono chunk, aggiungili al database
    if chunks:
        db.add_documents(chunks)

    db.persist()
    return db  # Restituisce il database Chroma, anche se vuoto
