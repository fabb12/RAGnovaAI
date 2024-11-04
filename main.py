# main.py

import streamlit as st
from database import load_or_create_chroma_db
from utils.retriever import query_rag
from utils.formatter import format_response  # Importa la funzione aggiornata
from ui_components import apply_custom_css
from config import API_KEY
import os

# Configura la pagina per usare tutta la larghezza disponibile
st.set_page_config(layout="wide")

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
            # Ottieni la risposta e i documenti di riferimento
            answer, references = query_rag(question)

            # Normalizza la risposta usando la funzione di formattazione
            formatted_answer = format_response(answer, references)

            # Visualizza la risposta in formato Markdown
            st.markdown(formatted_answer)
    else:
        st.warning("Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

# Se l'utente seleziona "Gestione Documenti", chiama la funzione `show_manage_documents_page`
elif page == "Gestione Documenti":
    from manage_documents import show_manage_documents_page
    show_manage_documents_page(vector_store)
