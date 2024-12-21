# app.py

import os
import json
import uuid
import logging
import streamlit as st
import validators
from dotenv import load_dotenv

from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, DEFAULT_MODEL
from database import load_or_create_chroma_db
from document_interface import DocumentInterface
from ui_components import apply_custom_css
from utils.processing.retriever import query_rag_with_gpt, query_rag_with_cloud
from utils.formatting.formatter import format_response
from langchain_community.document_loaders import WebBaseLoader

# Gestione dei token di sessione per gli utenti loggati
SESSION_TOKENS = {}

def load_users():
    """Carica il file degli utenti con le credenziali."""
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)


class FinanceQAApp:
    def __init__(self, config_file='app_config.txt'):
        # Carica variabili di ambiente
        load_dotenv()

        # Carica la configurazione personalizzata
        self.config = self.load_config(config_file)

        # Configura la pagina Streamlit
        st.set_page_config(
            page_title=self.config.get('page_title', 'Finance Q&A'),
            layout="wide",
            page_icon=self.config.get('page_icon', '💬')
        )

        # Applica il CSS personalizzato
        apply_custom_css()

        # Inizializza lo stato
        self.initialize_session_state()

        # Scelta della pagina: Domande o Gestione Documenti
        self.page = None

        self.vector_store = None
        self.doc_interface = None

    def load_config(self, filename):
        """Carica il file di configurazione chiave=valore."""
        config = {}
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key.strip()] = value.strip()
        return config

    def initialize_session_state(self):
        if "use_previous_answer" not in st.session_state:
            st.session_state["use_previous_answer"] = False
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "previous_answer" not in st.session_state:
            st.session_state["previous_answer"] = ""
        if "current_question" not in st.session_state:
            st.session_state["current_question"] = ""
        # Inizializza lo stato di login
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False
        if "username" not in st.session_state:
            st.session_state["username"] = None

    def setup_sidebar(self):
        """Configura la barra laterale: navigazione, modello AI, cronologia, logout."""
        st.sidebar.title(self.config.get('sidebar_navigation', '📚 Navigazione'))
        st.sidebar.divider()

        # Scelta del modello AI
        model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
        default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
        self.model_choice = st.sidebar.selectbox("Modello", model_options, index=default_index)

        # Controllo chiavi API
        if self.model_choice == "GPT (OpenAI)" and not OPENAI_API_KEY:
            st.sidebar.error("🔑 Chiave API OpenAI non impostata.")
        elif self.model_choice == "Claude (Anthropic)" and not ANTHROPIC_API_KEY:
            st.sidebar.error("🔑 Chiave API Anthropic non impostata.")

        # Toggle uso risposta precedente come contesto
        st.session_state["use_previous_answer"] = st.sidebar.checkbox(
            "Usa contesto della risposta precedente",
            value=st.session_state["use_previous_answer"],
            help="Includi la risposta precedente come contesto."
        )
        if not st.session_state["use_previous_answer"]:
            st.session_state["previous_answer"] = ""

        st.sidebar.divider()
        self.display_history_in_sidebar()

    def display_history_in_sidebar(self):
        """Mostra la cronologia nella barra laterale."""
        st.sidebar.markdown(f"### {self.config.get('sidebar_history', '📜 Cronologia delle Domande')}")
        if st.session_state["history"]:
            for i, entry in enumerate(reversed(st.session_state["history"])):
                with st.sidebar.expander(f"❓ {entry['question']}", expanded=False):
                    st.markdown(f"**Risposta:** {entry['answer']}")
                    if entry["references"]:
                        st.markdown("**Riferimenti:**")
                        for source, name in entry["references"]:
                            st.markdown(f"- **{name}** ({source})")
                    if st.button("Usa", key=f"history_button_{i}"):
                        st.session_state["current_question"] = entry["question"]
        else:
            st.sidebar.info("La cronologia è vuota.")

    def handle_user_login(self):
        """Gestisce il login dell'utente tramite username/password o token di sessione."""
        query_params = st.query_params
        token = query_params.get("token", [None])[0]

        # Controllo token di sessione
        if token and token in SESSION_TOKENS:
            st.session_state["logged_in"] = True
            st.session_state["username"] = SESSION_TOKENS[token]
        else:
            if "logged_in" not in st.session_state:
                st.session_state["logged_in"] = False
            if "username" not in st.session_state:
                st.session_state["username"] = None
        # Se non loggato, mostra il form di login
        if not st.session_state.get("logged_in", False):
            st.title("Accesso Utente")
            with st.form(key="login_form"):
                # Normalizzazione dell'username: spazi rimossi e trasformato in maiuscolo
                username = st.text_input("Username").strip().upper()
                password = st.text_input("Password", type="password").strip()
                submit_button = st.form_submit_button("Login")

            if submit_button:
                users = load_users()  # Funzione che carica gli utenti registrati

                # Normalizzazione chiavi del dizionario `users` per supportare la comparazione
                normalized_users = {key.upper(): value.strip() for key, value in users.items()}

                # Verifica credenziali
                if username in normalized_users and password == normalized_users[username]:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    self.load_user_history(username)

                    # Genera un token univoco per la sessione
                    session_token = str(uuid.uuid4())
                    SESSION_TOKENS[session_token] = username

                    # Imposta i parametri della query con il token di sessione
                    st.query_params = {"token":session_token}

                else:
                    st.error("Credenziali non valide.")

            st.stop()

    def load_user_history(self, username):
        """Carica la cronologia dell'utente da file."""
        user_history_file = f"chat_log_{username}.txt"
        if os.path.exists(user_history_file):
            with open(user_history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
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
        """Salva la cronologia dell'utente su file."""
        user_history_file = f"chat_log_{username}.txt"
        with open(user_history_file, "w", encoding="utf-8") as f:
            for entry in st.session_state["history"]:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_interaction(self, question, context, formatted_context, answer, history):
        """Logga le interazioni su file di log."""
        logging.info("Domanda: %s", question)
        logging.info("Contesto fornito: %s", context)
        logging.info("Contesto formattato: %s", formatted_context)
        logging.info("Risposta: %s", answer)
        logging.info("Cronologia: %s", history)

    def add_to_history(self, question, answer, references):
        """Aggiunge una nuova interazione alla cronologia."""
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

    def logout_user(self, token):
        """Effettua il logout dell'utente."""
        if token and token in SESSION_TOKENS:
            del SESSION_TOKENS[token]
        st.query_params = {}
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["history"] = []
        st.rerun()

    def select_knowledge_base(self, username):
        """Seleziona la Knowledge Base disponibile per l'utente."""
        kb_list = [
            name.replace(f"chroma_{username}_", "")
            for name in os.listdir(".")
            if name.startswith(f"chroma_{username}_")
        ]
        st.session_state["knowledge_bases"] = kb_list

        if "selected_kb" not in st.session_state:
            st.session_state["selected_kb"] = kb_list[0] if kb_list else None

        st.sidebar.divider()
        st.sidebar.markdown("### 📚 Seleziona Knowledge Base")
        if kb_list:
            selected_kb = st.sidebar.selectbox(
                "Knowledge Base",
                kb_list,
                index=kb_list.index(st.session_state["selected_kb"]) if st.session_state["selected_kb"] in kb_list else 0
            )
            # Aggiorna la KB selezionata se diversa dalla precedente
            if st.session_state.get("selected_kb") != selected_kb:
                st.session_state["selected_kb"] = selected_kb
        else:
            st.sidebar.info("Non ci sono Knowledge Base disponibili. Creane una nella sezione 'Gestione Documenti'.")

    def load_vector_store(self, username):
        """Carica o crea il vector store in base alla KB selezionata."""
        if st.session_state['selected_kb']:
            full_kb_name = f"{username}_{st.session_state['selected_kb']}"
            return load_or_create_chroma_db(full_kb_name)
        return None

    def load_web_content(self, url):
        """Carica contenuti da un URL tramite WebBaseLoader."""
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            return documents
        except Exception as e:
            st.error(f"Errore durante il caricamento del contenuto web: {e}")
            return None

    def handle_documents_page(self):
        """Gestisce la pagina di gestione documenti."""
        st.header(self.config.get('header_documents', "📚 Gestione Knowledge Base"))
        st.markdown(self.config.get(
            'default_document_message',
            "Carica, visualizza e gestisci i documenti nella knowledge base."
        ))
        self.doc_interface.show()

    def handle_questions_page(self):
        """Gestisce la pagina delle domande."""
        st.header("🚀 Benvenuto nel sistema RAGnova!")
        st.subheader(
            "💬 CIAO, {}! \n Inserisci una domanda per esplorare rapidamente la documentazione interna.".format(
                st.session_state['username'].upper()
            )
        )
        selected_kb_display = st.session_state.get("selected_kb", "Nessuna Knowledge Base selezionata")
        st.markdown(f"**Knowledge Base selezionata:** {selected_kb_display}")

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

        # Se l'input è un URL, carica i contenuti da web
        if validators.url(question):
            st.info("Riconosciuto come URL. Caricamento contenuti dal sito web...")
            self.doc_interface.add_web_document(question)
            st.success("Contenuto web caricato correttamente.")
        elif self.vector_store and question:
            # Includi la risposta precedente se necessario
            if st.session_state["use_previous_answer"] and st.session_state["previous_answer"]:
                question_with_context = f"{st.session_state['previous_answer']}\n\nDomanda attuale: {question}"
            else:
                question_with_context = question

            # Query al modello selezionato
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

            format_response(answer, references, self.doc_interface.doc_manager)
            self.add_to_history(question, answer, references)
            self.save_user_history(st.session_state["username"])

            self.log_interaction(
                question,
                question_with_context,
                question_with_context,
                answer,
                st.session_state["history"]
            )

            # Aggiorna la risposta precedente se il contesto è attivo
            if st.session_state["use_previous_answer"]:
                st.session_state["previous_answer"] = answer

            st.session_state["current_question"] = ""
            st.divider()
        elif not self.vector_store:
            st.warning("🚨 Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

    def run(self):
        # Gestisce login
        self.handle_user_login()

        if st.session_state["logged_in"]:
            self.setup_sidebar()
            username = st.session_state["username"]
            self.vector_store = self.load_vector_store(username)

            # Inizializza o aggiorna doc_interface
            if not self.doc_interface:
                self.doc_interface = DocumentInterface(self.vector_store)
            else:
                self.doc_interface.update_vector_store(self.vector_store)

            # Ora puoi chiamare le pagine
            if self.page == "❓ Domande":
                self.handle_questions_page()
            elif self.page == "🗂️ Gestione Documenti":
                self.handle_documents_page()

    def setup_sidebar(self):
        """Configura la barra laterale: navigazione, modello AI, Knowledge Base, cronologia."""
        if st.session_state["logged_in"]:
            username = st.session_state["username"]

            # 1) Navigazione
            st.sidebar.title(self.config.get('sidebar_navigation', '📚 Navigazione'))
            st.sidebar.divider()
            self.page = st.sidebar.radio("Vai a:", ["❓ Domande", "🗂️ Gestione Documenti"])

            # 2) Scelta del modello AI
            model_options = ["GPT (OpenAI)", "Claude (Anthropic)"]
            default_index = model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0
            self.model_choice = st.sidebar.selectbox("Modello", model_options, index=default_index)

            # Controllo chiavi API
            if self.model_choice == "GPT (OpenAI)" and not OPENAI_API_KEY:
                st.sidebar.error("🔑 Chiave API OpenAI non impostata.")
            elif self.model_choice == "Claude (Anthropic)" and not ANTHROPIC_API_KEY:
                st.sidebar.error("🔑 Chiave API Anthropic non impostata.")

            # Toggle uso risposta precedente come contesto
            st.session_state["use_previous_answer"] = st.sidebar.checkbox(
                "Usa contesto della risposta precedente",
                value=st.session_state["use_previous_answer"],
                help="Includi la risposta precedente come contesto."
            )
            if not st.session_state["use_previous_answer"]:
                st.session_state["previous_answer"] = ""


            # 3) Seleziona Knowledge Base
            self.select_knowledge_base(username)

            st.sidebar.divider()

            # 4) Cronologia
            self.display_history_in_sidebar()

            st.sidebar.divider()

            # Logout
            query_params = st.query_params
            token = query_params.get("token", [None])[0]

            col_user, col_logout = st.sidebar.columns([2, 1])
            with col_user:
                st.markdown(
                    f"<span style='font-weight:bold; font-size:1.3em; color:#FFFFFF; background-color:#333333; padding:4px 8px; border-radius:5px;'>👤 {username}</span>",
                    unsafe_allow_html=True
                )
            with col_logout:
                if st.button("🚪 Logout"):
                    self.logout_user(token)

            st.sidebar.divider()
    @staticmethod
    def main():
        app = FinanceQAApp()
        app.run()


if __name__ == "__main__":
    FinanceQAApp.main()
