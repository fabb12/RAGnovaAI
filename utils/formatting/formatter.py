# formatter.py

import platform
import subprocess
import os
import streamlit as st
import validators
def format_response(answer, references):
    """
    Formatta la risposta in Markdown e aggiunge i documenti di riferimento con il nome e un pulsante per aprirli.

    Parameters:
    - answer (str): Il testo della risposta generata dall'IA.
    - references (list of dict): Un elenco di dizionari con dettagli dei documenti di riferimento.

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

        # Crea una riga per ogni documento, con nome e pulsante/link
        for ref_key, file_name in unique_references.items():
            col1, col2 = st.columns([4, 1])  # Layout con due colonne
            with col1:
                if validators.url(ref_key):
                    # Mostra la fonte come link cliccabile
                    st.markdown(f"- **[{file_name}]({ref_key})**", unsafe_allow_html=True)
                else:
                    st.markdown(f"- **{file_name}**")  # Mostra il nome del file

            with col2:
                if not validators.url(ref_key):
                    # Aggiungi il pulsante "Apri" per i file locali
                    if os.path.exists(ref_key):
                        if st.button("Apri", key=ref_key):
                            open_file(ref_key)
                    else:
                        st.warning("File non trovato")
    else:
        st.markdown("Nessun documento di riferimento trovato.")


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
