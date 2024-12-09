#app.py

import streamlit as st
from dotenv import load_dotenv
import logging
import validators  # Per validare gli URL
from database import load_or_create_chroma_db
from document_interface import DocumentInterface
from utils.processing.retriever import query_rag_with_gpt, query_rag_with_cloud
from utils.formatting.formatter import format_response
from ui_components import apply_custom_css
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, DEFAULT_MODEL
from langchain_community.document_loaders import WebBaseLoader  # Per caricare contenuti web
import os
import uuid
import json


SESSION_TOKENS = {}
def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)
    return users

class FinanceQAApp:
    def __init__(self, config_file='app_config.txt'):

        # Carica le variabili di ambiente dal file `.env`
        load_dotenv()

        # Carica la configurazione dal file txt
        self.config = self.load_config(config_file)

        # Configura la pagina per usare tutta la larghezza disponibile e icona
        st.set_page_config(
            page_title=self.config.get('page_title', 'Finance Q&A'),
            layout="wide",
            page_icon=self.config.get('page_icon', '💬')
        )

        # Applica il CSS personalizzato
        apply_custom_css()


        # Inizializza le knowledge base
        if "knowledge_bases" not in st.session_state:
            kb_list = [name.replace("chroma_", "") for name in os.listdir(".") if name.startswith("chroma_")]
            st.session_state["knowledge_bases"] = kb_list
        if "selected_kb" not in st.session_state:
            st.session_state["selected_kb"] = st.session_state["knowledge_bases"][0] if st.session_state["knowledge_bases"] else None


        # Configura lo stato del toggle per previous_answer
        if "use_previous_answer" not in st.session_state:
            st.session_state["use_previous_answer"] = False  # Disabilitato di default

        # Configurazione dello stato della sessione
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "previous_answer" not in st.session_state:
            st.session_state["previous_answer"] = ""
        if "current_question" not in st.session_state:
            st.session_state["current_question"] = ""

        # Barra laterale con navigazione e cronologia
        st.sidebar.title(self.config.get('sidebar_navigation', '📚 Navigazione'))
        self.page = st.sidebar.radio("Vai a:", ["❓ Domande", "🗂️ Gestione Documenti"])

        st.sidebar.divider()


        # Gestione della selezione della Knowledge Base
        st.sidebar.markdown("### 📚 Seleziona Knowledge Base")
        kb_list = st.session_state.get("knowledge_bases", [])
        if kb_list:
            selected_kb = st.sidebar.selectbox(
                "Knowledge Base",
                kb_list,
                index=kb_list.index(st.session_state["selected_kb"]) if st.session_state.get(
                    "selected_kb") in kb_list else 0
            )
            if st.session_state.get("selected_kb") != selected_kb:
                st.session_state["selected_kb"] = selected_kb
        else:
            st.sidebar.info("Non ci sono Knowledge Base disponibili. Creane una nella sezione 'Gestione Documenti'.")


        st.sidebar.divider()

        # Selezione del modello di intelligenza artificiale
        st.sidebar.markdown("### Modello Intelligenza Artificiale")
        model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
        default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
        self.model_choice = st.sidebar.selectbox("Seleziona il modello", model_options, index=default_index)

        # Verifica chiavi API
        if self.model_choice == "GPT (OpenAI)" and not OPENAI_API_KEY:
            st.sidebar.error("🔑 Chiave API OpenAI non impostata.")
        elif self.model_choice == "Claude (Anthropic)" and not ANTHROPIC_API_KEY:
            st.sidebar.error("🔑 Chiave API Anthropic non impostata.")

        # Toggle per abilitare o disabilitare l'uso del contesto della risposta precedente
        st.session_state["use_previous_answer"] = st.sidebar.checkbox(
            "Usa contesto della risposta precedente",
            value=st.session_state["use_previous_answer"],
            help="Attiva per includere la risposta precedente come contesto."
        )

        # Ripulisce il contesto precedente se il toggle è disabilitato
        if not st.session_state["use_previous_answer"]:
            st.session_state["previous_answer"] = ""

        st.sidebar.divider()
        # Mostra la cronologia nella barra laterale
        self.display_history()

    def load_config(self, filename):
        """Carica il file di configurazione."""
        config = {}
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key.strip()] = value.strip()
        return config

    def log_interaction(self, question, context, formatted_context, answer, history):
        """Registra i dettagli di ogni interazione nel file di log."""
        logging.info("Domanda: %s", question)
        logging.info("Contesto fornito: %s", context)
        logging.info("Contesto formattato per il modello: %s", formatted_context)
        logging.info("Risposta: %s", answer)
        logging.info("Cronologia: %s", history)

    def add_to_history(self, question, answer, references):
        """Aggiunge una nuova domanda e risposta alla cronologia nella sessione."""
        unique_references = {}
        for ref in references:
            source = ref.get("source_url", ref.get("file_path", "Sconosciuto"))
            unique_references[source] = ref.get("file_name", "Web Content")

        history_entry = {
            "question": question,
            "answer": answer,
            "references": list(unique_references.items())
        }
        st.session_state["history"].append(history_entry)

    def load_user_history(self, username):
        """Carica la cronologia per l'utente specificato da file."""
        user_history_file = f"chat_log_{username}.txt"
        if os.path.exists(user_history_file):
            with open(user_history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Ogni entry sarà salvata in un formato strutturato (es. JSON)
            # Assumiamo di salvare la cronologia in JSON lines per semplicità:
            import json
            history = []
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    history.append(entry)
                except:
                    pass
            st.session_state["history"] = history
        else:
            st.session_state["history"] = []

    def save_user_history(self, username):
        """Salva la cronologia corrente dell'utente su file."""
        user_history_file = f"chat_log_{username}.txt"
        import json
        with open(user_history_file, "w", encoding="utf-8") as f:
            for entry in st.session_state["history"]:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")


    def display_history(self):
        """Visualizza la cronologia nella barra laterale."""
        st.sidebar.markdown(f"### {self.config.get('sidebar_history', '📜 Cronologia delle Domande')}")
        if st.session_state["history"]:
            for i, entry in enumerate(reversed(st.session_state["history"])):
                with st.sidebar.expander(f"❓ {entry['question']}", expanded=False):
                    st.markdown(f"**Risposta:** {entry['answer']}")
                    if entry["references"]:
                        st.markdown("**Riferimenti:**")
                        for source, name in entry["references"]:
                            st.markdown(f"- **{name}** ({source})")
                    if st.button(f"Usa", key=f"history_button_{i}"):
                        st.session_state["current_question"] = entry["question"]

        else:
            st.sidebar.info("La cronologia è vuota.")

    def load_web_content(self, url):
        """Scarica e restituisce i contenuti di una pagina web per l'elaborazione."""
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            return documents
        except Exception as e:
            st.error(f"Errore durante il caricamento del contenuto web: {e}")
            return None

    def run(self):

        # Controlla se c'è un token nell'URL
        query_params = st.query_params
        token = query_params.get("token", [None])[0]

        # Se il token esiste e risulta valido, salta la login
        if token and token in SESSION_TOKENS:
            st.session_state["logged_in"] = True
            st.session_state["username"] = SESSION_TOKENS[token]
        else:
            if "logged_in" not in st.session_state:
                st.session_state["logged_in"] = False
            if "username" not in st.session_state:
                st.session_state["username"] = None

        if not st.session_state["logged_in"]:
            st.title("Accesso Utente")
            with st.form(key="login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Login")

            if submit_button:
                users = load_users()
                if username in users and password == users[username]:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    self.load_user_history(username)

                    # Genera un token e memorizzalo
                    session_token = str(uuid.uuid4())
                    SESSION_TOKENS[session_token] = username
                    # Imposta parametri URL con il token
                    # Codice aggiornato con st.query_params.from_dict
                    st.query_params.from_dict({"token": session_token})

                    # Ora se l'utente fa refresh, il token rimane nell'URL
                else:
                    st.error("Credenziali non valide.")
            st.stop()

        else:
            # Visualizza il nome dell'utente e il pulsante "Logout" nella barra laterale
            with st.sidebar:
                cols = st.columns([3, 1])
                cols[0].markdown(f"**Utente:** {st.session_state['username']}")
                if cols[1].button("Logout"):
                    if token and token in SESSION_TOKENS:
                        del SESSION_TOKENS[token]
                    # Rimuovi il token dall'URL
                    st.query_params.clear()
                    st.session_state["logged_in"] = False
                    st.session_state["username"] = None
                    st.session_state["history"] = []
                    st.rerun()


            # Inizializza o aggiorna il vector store e il document interface in base alla KB selezionata
            self.vector_store = load_or_create_chroma_db(st.session_state["selected_kb"])
            if not hasattr(self, 'doc_interface') or self.doc_interface is None:
                self.doc_interface = DocumentInterface(self.vector_store)
            else:
                self.doc_interface.update_vector_store(self.vector_store)

            if self.page == "❓ Domande":
                st.header(self.config.get('header_questions', "💬 Fai una Domanda"))

                # Mostra la knowledge base selezionata
                selected_kb = st.session_state.get("selected_kb", "Nessuna Knowledge Base selezionata")
                st.markdown(f"**Knowledge Base selezionata:** {selected_kb}")

                col1, col2 = st.columns([3, 1])

                with col1:
                    question = st.text_input(
                        self.config.get('default_question_placeholder', "📝 Inserisci la tua domanda o URL:"),
                        max_chars=500,
                        help="Digita una domanda o inserisci un URL per elaborare contenuti web.",
                        value=st.session_state.get("current_question", "")
                    )

                with col2:
                    expertise_level = st.selectbox(
                        "Livello competenza",
                        ["beginner", "intermediate", "expert"],
                        index=2,
                        help="Scegli il livello per adattare il dettaglio della risposta."
                    )

                if validators.url(question):  # Se la domanda è un URL
                    st.info("Riconosciuto come URL. Caricamento contenuti dal sito web...")
                    self.doc_interface.add_web_document(question)
                    st.success("Contenuto web caricato correttamente.")
                elif self.vector_store and question:
                    # Usa il contesto della risposta precedente se abilitato
                    if st.session_state["use_previous_answer"] and st.session_state["previous_answer"]:
                        question_with_context = (
                            f"{st.session_state['previous_answer']} \n\nDomanda attuale: {question}"
                        )
                    else:
                        question_with_context = question

                    # Esegui la query
                    if self.model_choice == "GPT (OpenAI)" and OPENAI_API_KEY:
                        answer, references = query_rag_with_gpt(
                            question_with_context,
                            self.vector_store,
                            expertise_level=expertise_level
                        )
                    elif self.model_choice == "Claude (Anthropic)" and ANTHROPIC_API_KEY:
                        answer, references, _, _ = query_rag_with_cloud(
                            question_with_context,
                            self.vector_store,
                            expertise_level=expertise_level
                        )
                    else:
                        answer = "⚠️ La chiave API per il modello selezionato non è disponibile."
                        references = []

                    # Mostra la risposta
                    format_response(answer, references)

                    # Aggiungi alla cronologia e salva
                    self.add_to_history(question, answer, references)
                    self.save_user_history(st.session_state["username"])

                    # Log dell'interazione
                    self.log_interaction(
                        question,
                        question_with_context,
                        question_with_context,
                        answer,
                        st.session_state["history"]
                    )

                    # Aggiorna la risposta precedente se abilitato
                    if st.session_state["use_previous_answer"]:
                        st.session_state["previous_answer"] = answer

                    # Reset della domanda corrente
                    st.session_state["current_question"] = ""
                    st.divider()
                elif not self.vector_store:
                    st.warning(
                        "🚨 Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

            elif self.page == "🗂️ Gestione Documenti":
                st.header(self.config.get('header_documents', "📚 Gestione Knowledge Base"))
                st.markdown(self.config.get(
                    'default_document_message',
                    "Carica, visualizza e gestisci i documenti nella knowledge base."
                ))
                self.doc_interface.show()

    @staticmethod
    def main():
        app = FinanceQAApp()
        app.run()


# Esegui l'applicazione
if __name__ == "__main__":
    FinanceQAApp.main()
