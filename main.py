# main.py

import streamlit as st
from database import load_or_create_chroma_db
from utils.retriever import query_rag_with_gpt, query_rag_with_cloud
from utils.formatter import format_response
from ui_components import apply_custom_css
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, DEFAULT_MODEL
import os
from dotenv import load_dotenv

# Carica le variabili di ambiente dal file `.env`
load_dotenv()

# Configura la pagina per usare tutta la larghezza disponibile
st.set_page_config(layout="wide")

# Applica il CSS personalizzato
apply_custom_css()

# Inizializza o carica il database ChromaDB
vector_store = load_or_create_chroma_db()

# Configura la barra laterale per la navigazione e modello
st.sidebar.title("Navigazione")
page = st.sidebar.radio("Vai a", ["Domande", "Gestione Documenti"])

# Inizializza la cronologia e la risposta precedente se non già presenti nello stato di sessione
if "history" not in st.session_state:
    st.session_state["history"] = []

if "previous_answer" not in st.session_state:
    st.session_state["previous_answer"] = ""

# Selezione del modello di intelligenza artificiale, predefinito con `DEFAULT_MODEL`
model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
model_choice = st.sidebar.selectbox("Seleziona il modello di intelligenza artificiale", model_options, index=default_index)

# Mostra la cronologia nella barra laterale con l'ordine più recente in alto
st.sidebar.subheader("Cronologia delle Domande")
for i, entry in enumerate(reversed(st.session_state["history"])):
    st.sidebar.markdown(f"**{i + 1}. {entry['question']}**")
    st.sidebar.caption(entry["answer"])

# Verifica la presenza delle chiavi API solo per il modello selezionato
if model_choice == "GPT (OpenAI)":
    if not OPENAI_API_KEY:
        st.warning("La chiave API di OpenAI non è impostata. Verifica il file `.env` o inseriscila nella sidebar.")

elif model_choice == "Claude (Anthropic)":
    if not ANTHROPIC_API_KEY:
        st.warning("La chiave API di Anthropic non è impostata. Verifica il file `.env` o inseriscila nella sidebar.")

# Sezione Domande e Risposte
if page == "Domande":
    st.header("Fai una Domanda su Master Finance")
    if vector_store:
        question = st.text_input("Inserisci la tua domanda:", max_chars=500)

        if question:
            # Aggiungi il contesto della risposta precedente, se esiste
            question_with_context = f"{st.session_state['previous_answer']} \n\nDomanda attuale: {question}" if st.session_state["previous_answer"] else question

            # Esegui la query basata sulla scelta del modello
            if model_choice == "GPT (OpenAI)" and OPENAI_API_KEY:
                answer, references = query_rag_with_gpt(question_with_context)
            elif model_choice == "Claude (Anthropic)" and ANTHROPIC_API_KEY:
                answer, references, _, _ = query_rag_with_cloud(question_with_context)
            else:
                answer = "La chiave API per il modello selezionato non è disponibile."
                references = []

            # Normalizza la risposta e i riferimenti per una migliore visualizzazione
            formatted_answer = format_response(answer, references)

            # Visualizza la risposta in Markdown
            st.markdown(formatted_answer)

            # Salva la domanda e risposta nella cronologia e aggiorna la risposta precedente
            st.session_state["history"].append({"question": question, "answer": formatted_answer})
            st.session_state["previous_answer"] = formatted_answer
    else:
        st.warning("Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

# Sezione per la gestione documenti
elif page == "Gestione Documenti":
    from manage_documents import show_manage_documents_page
    show_manage_documents_page(vector_store)
