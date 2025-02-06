# embeddings.py

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import os
import shutil
import logging

CHROMA_PATH = "chroma"

def create_embeddings(chunks, reset=False):
    logging.basicConfig(level=logging.INFO)
    if reset:
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
            logging.info(f"Cartella {CHROMA_PATH} resettata.")
    if not os.path.exists(CHROMA_PATH):
        logging.info("Creazione di un nuovo database Chroma.")
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=HuggingFaceEmbeddings()
        )
        if chunks:
            db.add_documents(chunks)
            db.persist()
        else:
            logging.info("Nessun documento da indicizzare.")
    else:
        logging.info("Caricamento del database Chroma esistente.")
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=HuggingFaceEmbeddings()
        )
        if chunks:
            db.add_documents(chunks)
            db.persist()
        else:
            logging.info("Nessun nuovo documento da aggiungere.")
    return db
