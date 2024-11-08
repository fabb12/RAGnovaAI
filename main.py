import streamlit as st
import os
from dotenv import load_dotenv
import logging
from database import load_or_create_chroma_db
from document_interface import DocumentInterface
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
    """
    Registra i dettagli di ogni interazione nel file di log.
    """
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
doc_interface = DocumentInterface(vector_store)

# Configurazione dello stato della sessione
if "history" not in st.session_state:
    st.session_state["history"] = []
if "previous_answer" not in st.session_state:
    st.session_state["previous_answer"] = ""
if "current_question" not in st.session_state:
    st.session_state["current_question"] = ""

# Funzione per aggiungere una domanda e risposta alla cronologia
def add_to_history(question, answer, references):
    """
    Aggiunge una nuova domanda e risposta alla cronologia nella sessione.
    """
    # Elimina i duplicati nei riferimenti
    unique_references = {}
    for ref in references:
        file_name = ref["file_name"]
        file_path = ref["file_path"]
        if file_path not in unique_references:
            unique_references[file_path] = file_name

    references_text = "\n".join(
        [f"- [{name}](#{path})" for path, name in unique_references.items()]
    )

    history_entry = {
        "question": question,
        "answer": answer,
        "references": list(unique_references.items())  # Salva come lista di tuple (path, name)
    }
    st.session_state["history"].append(history_entry)

# Funzione per visualizzare la cronologia
def display_history():
    """
    Visualizza la cronologia nella barra laterale, in ordine inverso.
    Permette di selezionare una domanda con un menu a tre pallini.
    """
    st.sidebar.markdown("### 📜 Cronologia delle Domande")
    if st.session_state["history"]:
        for i, entry in enumerate(reversed(st.session_state["history"])):  # Ordine inverso
            with st.sidebar.expander(f"❓ {entry['question']}", expanded=False):
                st.markdown(f"**Risposta:** {entry['answer']}")
                if entry["references"]:
                    st.markdown("**Riferimenti:**")
                    for file_path, file_name in entry["references"]:
                        st.markdown(
                            f"- **{file_name}**",
                            help=f"Percorso: {file_path}"  # Mostra il tooltip sul nome
                        )
                # Aggiungi i tre pallini per selezionare una domanda
                if st.button("Usa", key=f"menu_{i}"):
                    st.session_state["current_question"] = entry["question"]
    else:
        st.sidebar.info("La cronologia è vuota.")

# Barra laterale con navigazione e cronologia
st.sidebar.title("📚 Navigazione")
page = st.sidebar.radio("Vai a:", ["❓ Domande", "🗂️ Gestione Documenti"])

st.sidebar.divider()


# Selezione del modello di intelligenza artificiale
st.sidebar.markdown("### Modello Intelligenza Artificiale")
model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
model_choice = st.sidebar.selectbox("Seleziona il modello", model_options, index=default_index)

# Verifica chiavi API
if model_choice == "GPT (OpenAI)" and not OPENAI_API_KEY:
    st.sidebar.error("🔑 Chiave API OpenAI non impostata.")
elif model_choice == "Claude (Anthropic)" and not ANTHROPIC_API_KEY:
    st.sidebar.error("🔑 Chiave API Anthropic non impostata.")
st.sidebar.divider()
# Mostra la cronologia nella barra laterale
display_history()

# Sezione Domande e Risposte
if page == "❓ Domande":
    st.header("💬 Fai una Domanda su Master Finance")
    st.markdown("Inserisci la tua domanda qui sotto per ricevere risposte personalizzate.")

    # Configura una riga con colonne per la domanda e il livello di competenza
    col1, col2 = st.columns([3, 1])

    with col1:
        # Precompila il campo della domanda se "Riproposta" è stato cliccato
        question = st.text_input(
            "📝 Inserisci la tua domanda:",
            max_chars=500,
            help="Digita la tua domanda qui",
            value=st.session_state.get("current_question", "")
        )

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

        # Esegui la query
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

        # Aggiungi domanda, risposta e riferimenti alla cronologia
        add_to_history(question, answer, references)

        # Salva la cronologia nel file di log
        log_interaction(question, question_with_context, question_with_context, answer, st.session_state["history"])

        # Aggiorna l'ultima risposta
        st.session_state["previous_answer"] = answer

        # Ripulisci la domanda corrente
        st.session_state["current_question"] = ""
        st.divider()
    elif not vector_store:
        st.warning("🚨 Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

# Sezione Gestione Documenti
elif page == "🗂️ Gestione Documenti":
    st.header("📁 Gestione Documenti")
    st.markdown("Carica, visualizza e gestisci i documenti nella knowledge base.")
    doc_interface.show()
