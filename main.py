# main.py

import streamlit as st

# Configura la pagina come prima istruzione
st.set_page_config(layout="wide")

from database import load_or_create_chroma_db
from utils.retriever import query_rag
from ui_components import apply_custom_css
from config import API_KEY
import os

# Applica il CSS personalizzato
apply_custom_css()

# Inizializza o carica il database ChromaDB
vector_store = load_or_create_chroma_db()

# Configura la barra laterale per la navigazione
st.sidebar.title("Navigazione")
page = st.sidebar.radio("Vai a", ["Domande", "Gestione Documenti"])

# Carica la chiave API di OpenAI
if API_KEY:
    os.environ['OPENAI_API_KEY'] = API_KEY
else:
    st.error("La chiave API di OpenAI non è impostata. Verifica il file `.env` o inseriscila nella sidebar.")

# Sezione Domande e Risposte
if page == "Domande":
    st.header("Fai una Domanda su Master Finance")
    if vector_store:
        question = st.text_input("Inserisci la tua domanda:", max_chars=500)
        if question:
            answer = query_rag(question)
            formatted_answer = f"""
            ### Risposta:

            {answer}

            ---
            """
            st.markdown(formatted_answer, unsafe_allow_html=True)
    else:
        st.warning("Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

# Se l'utente seleziona "Gestione Documenti", visualizza la pagina `manage_documents.py`
elif page == "Gestione Documenti":
    import manage_documents
