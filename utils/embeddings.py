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

