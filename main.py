import streamlit as st
import os
from dotenv import load_dotenv
import logging
from database import load_or_create_chroma_db
from document_interface import DocumentInterface  # Importa la nuova classe DocumentInterface
from utils.retriever import query_rag_with_gpt, query_rag_with_cloud
from utils.formatter import format_response
from ui_components import apply_custom_css
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, DEFAULT_MODEL

# Configura il logging per salvare tutte le domande e risposte
logging.basicConfig(
    filename="chat_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Funzione per il logging delle interazioni
def log_interaction(question, context, formatted_context, answer, history):
    logging.info("Domanda: %s", question)
    logging.info("Contesto fornito: %s", context)
    logging.info("Contesto formattato per il modello: %s", formatted_context)
    logging.info("Risposta: %s", answer)
    logging.info("Cronologia: %s", history)

# Carica le variabili di ambiente dal file `.env`
load_dotenv()

# Configura la pagina per usare tutta la larghezza disponibile e icona
st.set_page_config(page_title="Master Finance Q&A", layout="wide", page_icon="💬")

# Applica il CSS personalizzato
apply_custom_css()

# Inizializza il database e l'interfaccia documenti
vector_store = load_or_create_chroma_db()
doc_interface = DocumentInterface(vector_store)  # Istanzia DocumentInterface

# Barra laterale con icone e opzioni di navigazione
st.sidebar.title("📚 Navigazione")
page = st.sidebar.radio("Vai a:", ["❓ Domande", "🗂️ Gestione Documenti"])

# Divider per separare le sezioni
st.sidebar.divider()

# Selezione del modello di intelligenza artificiale
st.sidebar.markdown("### Modello Intelligenza Artificiale")
model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
model_choice = st.sidebar.selectbox("Seleziona il modello", model_options, index=default_index)

# Verifica chiavi API con indicatori visivi
if model_choice == "GPT (OpenAI)" and not OPENAI_API_KEY:
    st.sidebar.error("🔑 Chiave API OpenAI non impostata.")
elif model_choice == "Claude (Anthropic)" and not ANTHROPIC_API_KEY:
    st.sidebar.error("🔑 Chiave API Anthropic non impostata.")

# Divider per separare la cronologia delle domande
st.sidebar.divider()

# Visualizzazione della cronologia delle domande
st.sidebar.markdown("### 📜 Cronologia delle Domande")
if "history" in st.session_state and st.session_state["history"]:
    for i, entry in enumerate(reversed(st.session_state["history"])):
        st.sidebar.markdown(f"**{i + 1}.** {entry['question']}")
        st.sidebar.caption(entry["answer"])

# Configurazione dello stato della sessione
if "history" not in st.session_state:
    st.session_state["history"] = []
if "previous_answer" not in st.session_state:
    st.session_state["previous_answer"] = ""

# Sezione Domande e Risposte
# Sezione Domande e Risposte
if page == "❓ Domande":
    st.header("💬 Fai una Domanda su Master Finance")

    st.markdown("Inserisci la tua domanda qui sotto per ricevere risposte personalizzate.")

    # Configura una riga con colonne per la domanda e il livello di competenza
    col1, col2 = st.columns([3, 1])  # La domanda occupa più spazio rispetto al selettore

    with col1:
        question = st.text_input("📝 Inserisci la tua domanda:", max_chars=500, help="Digita la tua domanda qui")

    with col2:
        expertise_level = st.selectbox(
            "Livello competenza",
            ["beginner", "intermediate", "expert"],
            index=2,
            help="Scegli il livello per adattare il dettaglio della risposta."
        )

    if vector_store and question:
        question_with_context = (
            f"{st.session_state['previous_answer']} \n\nDomanda attuale: {question}"
            if st.session_state["previous_answer"] else question
        )

        # Esegui la query, includendo `expertise_level`
        if model_choice == "GPT (OpenAI)" and OPENAI_API_KEY:
            answer, references = query_rag_with_gpt(question_with_context, expertise_level=expertise_level)
        elif model_choice == "Claude (Anthropic)" and ANTHROPIC_API_KEY:
            answer, references, _, _ = query_rag_with_cloud(question_with_context, expertise_level=expertise_level)
        else:
            answer = "⚠️ La chiave API per il modello selezionato non è disponibile."
            references = []

        # Mostra la risposta e aggiorna cronologia
        formatted_answer = format_response(answer, references)
        st.markdown(formatted_answer)

        st.session_state["history"].append({"question": question, "answer": formatted_answer})
        st.session_state["previous_answer"] = formatted_answer
        log_interaction(
            question, question_with_context, question_with_context, formatted_answer, st.session_state["history"]
        )
        st.divider()
    elif not vector_store:
        st.warning("🚨 Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")


# Sezione Gestione Documenti
elif page == "🗂️ Gestione Documenti":
    st.header("📁 Gestione Documenti")
    st.markdown("Carica, visualizza e gestisci i documenti nella knowledge base.")
    doc_interface.show()
