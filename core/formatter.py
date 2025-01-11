import platform
import subprocess
import os
import streamlit as st
import validators
import mimetypes
import base64
import requests
from bs4 import BeautifulSoup
from functools import lru_cache


@lru_cache(maxsize=128)
def get_website_title(url):
    """
    Estrae il titolo del sito web dato un URL.

    Parameters:
    - url (str): L'URL del sito web.

    Returns:
    - str: Il titolo del sito web o l'URL stesso se non riesce a estrarlo.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
    except Exception as e:
        st.error(f"Errore nell'estrazione del titolo dal sito {url}: {e}")
    return url  # Ritorna l'URL se non riesce a estrarre il titolo


def format_response(answer, references, document_manager):
    """
    Formatta la risposta in Markdown e aggiunge i documenti di riferimento con il nome,
    un link per aprirli in una nuova scheda se sono PDF, e un pulsante per scaricarli.

    Parameters:
    - answer (str): Il testo della risposta generata dall'IA.
    - references (list of dict): Un elenco di dizionari con dettagli dei documenti di riferimento.
    - document_manager (DocumentManager): L'istanza di DocumentManager per accedere ai documenti.

    Returns:
    - None: La funzione stampa direttamente nella UI di Streamlit.
    """
    # Mostra la risposta generata
    st.markdown(f"### 📝 Risposta\n\n{answer}\n\n---")

    if references:
        st.markdown("### 📄 Documenti di Riferimento")
        unique_references = {}

        # Filtra i duplicati
        for ref in references:
            file_name = ref.get("file_name", "Documento sconosciuto")
            file_path = ref.get("file_path", None)
            source_url = ref.get("source_url", None)

            # Determina se è un file o un URL
            if source_url:
                if source_url not in unique_references:
                    unique_references[source_url] = file_name
            elif file_path:
                if file_path not in unique_references:
                    unique_references[file_path] = file_name

        # Crea una riga per ogni documento, con nome e pulsanti/link
        for ref_key, file_name in unique_references.items():
            col1, col2, col3 = st.columns([3, 1, 1])  # Layout con tre colonne
            with col1:
                if validators.url(ref_key):
                    # Ottieni il titolo del sito web
                    title = get_website_title(ref_key)

                    # Verifica se il file è un PDF
                    mime_type, _ = mimetypes.guess_type(ref_key)
                    if mime_type == "application/pdf":
                        # Crea un link che apre il PDF in una nuova scheda usando base64
                        pdf_link = create_pdf_link(ref_key, title, document_manager)
                        st.markdown(f"- **{pdf_link}**", unsafe_allow_html=True)
                    else:
                        # Link standard che apre in una nuova scheda con il titolo
                        st.markdown(
                            f'- **<a href="{ref_key}" target="_blank">{title}</a>**',
                            unsafe_allow_html=True
                        )
                else:
                    # File locale
                    if file_name.lower().endswith('.pdf'):
                        # Crea un link PDF usando base64
                        pdf_link = create_pdf_link(ref_key, file_name, document_manager)
                        st.markdown(f"- **{pdf_link}**", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- **{file_name}**")  # Mostra il nome del file

            with col2:
                if not validators.url(ref_key):
                    # Aggiungi il pulsante "Apri" per i file locali
                    if os.path.exists(ref_key):
                        if st.button("Apri", key=f"open_{ref_key}"):
                            open_file(ref_key)
                    else:
                        st.warning("File non trovato")

            with col3:
                if not validators.url(ref_key):
                    # Aggiungi il pulsante "Download" per scaricare il file
                    if os.path.exists(ref_key):
                        with open(ref_key, "rb") as file:
                            file_data = file.read()
                        st.download_button(
                            label="📥 Scarica",
                            data=file_data,
                            file_name=os.path.basename(ref_key),
                            mime=mimetypes.guess_type(ref_key)[0] or "application/octet-stream",
                            key=f"download_{ref_key}"
                        )
                    else:
                        st.warning("File non trovato")
    else:
        st.markdown("Nessun documento di riferimento trovato.")


def create_pdf_link(file_path, file_name, document_manager):
    """
    Crea un link HTML per aprire un PDF in una nuova scheda del browser usando base64.

    Parameters:
    - file_path (str): Percorso assoluto del file PDF.
    - file_name (str): Nome del file PDF da mostrare nel link.
    - document_manager (DocumentManager): L'istanza di DocumentManager per accedere ai documenti.

    Returns:
    - str: Link HTML per aprire il PDF.
    """
    try:
        # Leggi il contenuto del file PDF
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        # Codifica in base64
        b64_pdf = base64.b64encode(pdf_data).decode()
        # Crea un URL data
        href = f'data:application/pdf;base64,{b64_pdf}'
        # Crea il link HTML
        link = f'<a href="{href}" target="_blank">{file_name}</a>'
        return link
    except Exception as e:
        st.error(f"Errore nella creazione del link PDF: {e}")
        return file_name  # Fallback al nome del file senza link


def open_file(file_path):
    """
    Apre un file utilizzando l'applicazione predefinita del sistema operativo.

    Parameters:
    - file_path (str): Percorso assoluto del file da aprire.

    Returns:
    - None
    """
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)  # Windows
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        else:  # Linux
            subprocess.call(["xdg-open", file_path])
    except Exception as e:
        st.error(f"Errore nell'apertura del file: {e}")
