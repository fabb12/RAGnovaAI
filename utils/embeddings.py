from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import shutil
import logging

CHROMA_PATH = "chroma"


def create_embeddings(chunks, reset=False):
    """
    Crea embeddings per i chunk e li salva nel database ChromaDB.

    Args:
        chunks (list): Lista di chunk di testo da indicizzare.
        reset (bool): Se True, elimina e ricrea il database esistente.

    Returns:
        Chroma: Oggetto Chroma con i documenti indicizzati.
    """
    # Imposta il logger
    logging.basicConfig(level=logging.INFO)

    # Gestione della directory esistente
    if reset:
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
            logging.info(f"Cartella {CHROMA_PATH} resettata.")

    # Crea o aggiorna il database Chroma
    if not os.path.exists(CHROMA_PATH):
        logging.info("Creazione di un nuovo database Chroma.")
        db = Chroma.from_documents(
            chunks,
            OpenAIEmbeddings(),
            persist_directory=CHROMA_PATH
        )
        db.persist()
    else:
        logging.info("Caricamento del database Chroma esistente.")
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=OpenAIEmbeddings()
        )
        db.add_documents(chunks)
        db.persist()

    return db  # Restituisce il database Chroma
