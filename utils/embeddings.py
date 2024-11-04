# utils/embeddings.py
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import shutil

CHROMA_PATH = "chroma"

def create_embeddings(chunks):
    """Crea embeddings per i chunk e li salva nel database ChromaDB."""
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)  # Pulisce la cartella esistente

    # Crea il database Chroma dai chunk
    db = Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH
    )
    db.persist()
    return db  # Restituisce il database Chroma


def delete_document(vector_store, doc_id):
    """
    Rimuove tutti i chunk associati a un doc_id specifico dal database vettoriale.

    :param vector_store: L'istanza del database Chroma.
    :param doc_id: L'ID del documento da rimuovere.
    """
    # Usa un filtro per rimuovere i chunk associati al documento con il doc_id specifico
    vector_store._collection.delete(where={"doc_id": doc_id})  # Utilizza il filtro per cercare nei metadati
    vector_store.persist()  # Salva le modifiche al database
