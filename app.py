# app.py

import os
import json
import uuid
import logging
import streamlit as st
import validators

from core.database import load_or_create_chroma_db
from ui.document_interface import DocumentInterface
from core.formatter import format_response
from ui.ui_components import apply_custom_css

# Gestione dei token di sessione per gli utenti loggati
SESSION_TOKENS = {}

def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)

class FinanceQAApp:
    def __init__(self, config_file='app_config.txt'):
        self.config = self.load_config(config_file)
        st.set_page_config(
            page_title=self.config.get('page_title', 'Finance Q&A'),
            layout="wide",
            page_icon=self.config.get('page_icon', '💬')
        )
        apply_custom_css()
        self.initialize_session_state()
        self.page = None
        self.vector_store = None
        self.doc_interface = None
        self.model_choice = None  # verrà impostato nella sidebar

    def load_config(self, filename):
        config = {}
        if os.path.exists(filename):
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
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False
        if "username" not in st.session_state:
            st.session_state["username"] = None

    def setup_sidebar(self):
        if st.session_state["logged_in"]:
            username = st.session_state["username"]
            st.sidebar.title(self.config.get('sidebar_navigation', '📚 Navigazione'))
            st.sidebar.divider()
            self.page = st.sidebar.radio("Vai a:", ["❓ Domande", "🗂️ Gestione Documenti"])

            # Selezione del modello: Cloud, Deepseek (Locale) o Gemma (Locale)
            model_options = ["Cloude (Antrophic)", "Deepseek (Locale)", "Gemma (Locale)"]
            self.model_choice = st.sidebar.selectbox("Modello", model_options, index=0)

            st.session_state["use_previous_answer"] = st.sidebar.checkbox(
                "Usa contesto della risposta precedente",
                value=st.session_state["use_previous_answer"],
                help="Includi la risposta precedente come contesto."
            )
            if not st.session_state["use_previous_answer"]:
                st.session_state["previous_answer"] = ""

            self.select_knowledge_base(username)
            st.sidebar.divider()
            self.display_history_in_sidebar()
            st.sidebar.divider()

            query_params = st.query_params
            token = query_params.get("token", [None])[0]
            col_user, col_logout = st.sidebar.columns([2, 1])
            with col_user:
                st.markdown(
                    f"<span style='font-weight:bold; font-size:1.3em; color:#FFFFFF; "
                    f"background-color:#333333; padding:4px 8px; border-radius:5px;'>"
                    f"👤 {username}</span>",
                    unsafe_allow_html=True
                )
            with col_logout:
                if st.button("🚪 Logout"):
                    self.logout_user(token)
            st.sidebar.divider()

    def display_history_in_sidebar(self):
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
        query_params = st.query_params
        token = query_params.get("token", [None])[0]
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
                username = st.text_input("Username").strip().upper()
                password = st.text_input("Password", type="password").strip()
                submit_button = st.form_submit_button("Login")
            if submit_button:
                users = load_users()
                normalized_users = {key.upper(): value.strip() for key, value in users.items()}
                if username in normalized_users and password == normalized_users[username]:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    self.load_user_history(username)
                    session_token = str(uuid.uuid4())
                    SESSION_TOKENS[session_token] = username
                    st.query_params = {"token": session_token}
                else:
                    st.error("Credenziali non valide.")
            st.stop()

    def load_user_history(self, username):
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
        user_history_file = f"chat_log_{username}.txt"
        with open(user_history_file, "w", encoding="utf-8") as f:
            for entry in st.session_state["history"]:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_interaction(self, question, context, formatted_context, answer, history):
        logging.info("Domanda: %s", question)
        logging.info("Contesto fornito: %s", context)
        logging.info("Contesto formattato: %s", formatted_context)
        logging.info("Risposta: %s", answer)
        logging.info("Cronologia: %s", history)

    def add_to_history(self, question, answer, references):
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
        if token and token in SESSION_TOKENS:
            del SESSION_TOKENS[token]
        st.query_params = {}
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["history"] = []
        st.rerun()

    def select_knowledge_base(self, username):
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
            if st.session_state.get("selected_kb") != selected_kb:
                st.session_state["selected_kb"] = selected_kb
        else:
            st.sidebar.info("Non ci sono Knowledge Base disponibili. Creane una nella sezione 'Gestione Documenti'.")

    def load_vector_store(self, username):
        if st.session_state['selected_kb']:
            full_kb_name = f"{username}_{st.session_state['selected_kb']}"
            return load_or_create_chroma_db(full_kb_name)
        return None

    def load_web_content(self, url):
        try:
            from langchain_community.document_loaders import WebBaseLoader
            loader = WebBaseLoader(url)
            documents = loader.load()
            return documents
        except Exception as e:
            st.error(f"Errore durante il caricamento del contenuto web: {e}")
            return None

    def handle_documents_page(self):
        st.header(self.config.get('header_documents', "📚 Gestione Knowledge Base"))
        st.markdown(self.config.get(
            'default_document_message',
            "Carica, visualizza e gestisci i documenti nella knowledge base."
        ))
        self.doc_interface.show()

    def handle_questions_page(self):
        st.header(f"Buongiorno, {st.session_state['username'].upper()}!")
        st.subheader(
            "Benvenuto nel sistema RAGnova! Inserisci una domanda per esplorare rapidamente la documentazione interna."
        )
        st.divider()

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
        st.divider()

        if validators.url(question):
            st.info("Riconosciuto come URL. Caricamento contenuti dal sito web...")
            self.doc_interface.add_web_document(question)
            st.success("Contenuto web caricato correttamente.")
        elif self.vector_store and question:
            if st.session_state["use_previous_answer"] and st.session_state["previous_answer"]:
                question_with_context = (
                    f"{st.session_state['previous_answer']}\n\nDomanda attuale: {question}"
                )
            else:
                question_with_context = question

            # Seleziona il modello in base alla scelta
            if self.model_choice == "Cloude (Antrophic)":
                from core.retriever import query_rag_with_cloud
                answer, references = query_rag_with_cloud(
                    question_with_context,
                    self.vector_store,
                    expertise_level=expertise_level
                )
            elif self.model_choice == "Deepseek (Locale)":
                from core.retriever_deepseek import query_rag_with_deepseek
                answer, references = query_rag_with_deepseek(
                    question_with_context,
                    self.vector_store,
                    expertise_level=expertise_level
                )
            elif self.model_choice == "Gemma (Locale)":
                from core.retriever_gemma import query_rag_with_gemma
                answer, references = query_rag_with_gemma(
                    question_with_context,
                    self.vector_store,
                    expertise_level=expertise_level
                )
            else:
                answer = "Modello non selezionato correttamente."
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

            if st.session_state["use_previous_answer"]:
                st.session_state["previous_answer"] = answer

            st.session_state["current_question"] = ""
            st.divider()
        elif not self.vector_store:
            st.warning("🚨 Nessuna knowledge base disponibile. Carica un documento nella sezione 'Gestione Documenti'.")

    def run(self):
        self.handle_user_login()
        if st.session_state["logged_in"]:
            self.setup_sidebar()
            username = st.session_state["username"]
            self.vector_store = self.load_vector_store(username)
            if not self.doc_interface:
                self.doc_interface = DocumentInterface(self.vector_store)
            else:
                self.doc_interface.update_vector_store(self.vector_store)
            if self.page == "❓ Domande":
                self.handle_questions_page()
            elif self.page == "🗂️ Gestione Documenti":
                self.handle_documents_page()

    @staticmethod
    def main():
        app = FinanceQAApp()
        app.run()

if __name__ == "__main__":
    FinanceQAApp.main()
