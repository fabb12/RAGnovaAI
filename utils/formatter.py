import streamlit as st
import os
import platform
import subprocess


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

            # Controlla che il percorso non sia vuoto e aggiungilo se unico
            if file_path and file_path not in unique_references:
                unique_references[file_path] = file_name

        # Crea una riga per ogni documento, con nome e pulsante
        for file_path, file_name in unique_references.items():
            col1, col2 = st.columns([4, 1])  # Layout con due colonne
            with col1:
                st.markdown(f"**{file_name}**")  # Mostra il nome del file
            with col2:
                if os.path.exists(file_path):
                    # Crea un pulsante per aprire il file
                    if st.button(f"Apri", key=file_path):
                        open_file(file_path)
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
        else:  # Linux
            subprocess.call(["xdg-open", file_path])
    except Exception as e:
        st.error(f"Errore nell'apertura del file: {e}")
