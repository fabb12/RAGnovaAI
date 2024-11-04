# database.py

import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import streamlit as st

CHROMA_PATH = "chroma"  # Percorso per il database ChromaDB

def load_or_create_chroma_db():
    """Carica o crea il database ChromaDB."""
    if os.path.exists(CHROMA_PATH):
        st.info("Caricamento della knowledge base esistente da ChromaDB...")
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=OpenAIEmbeddings())
    else:
        st.info("Non è stata trovata una knowledge base. Aggiungi documenti per crearne una nuova.")
        return None
