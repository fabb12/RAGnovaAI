import streamlit as st
import os
import platform
import subprocess
import validators

def format_response(answer, references):
    """
    Formatta la risposta in Markdown e aggiunge i documenti di riferimento con il nome
    e un pulsante per aprirli se locali o un link cliccabile se URL.

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

            # Aggiungi il riferimento basato sul tipo (file locale o URL)
            if source_url and source_url not in unique_references:
                unique_references[source_url] = file_name
            elif file_path and file_path not in unique_references:
                unique_references[file_path] = file_name

        # Crea una riga per ogni documento, con nome e pulsante/link
        for key, file_name in unique_references.items():
            col1, col2 = st.columns([4, 1])  # Layout con due colonne
            with col1:
                st.markdown(f"**{file_name}**")  # Mostra il nome del file
            with col2:
                if validators.url(key):  # Riferimento web (URL)
                    st.markdown(f"[Apri URL]({key})", unsafe_allow_html=True)
                elif os.path.exists(key):  # Riferimento locale (file)
                    if st.button(f"Apri", key=key):
                        open_file(key)
                else:
                    st.warning("Riferimento non valido o file non trovato")
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
