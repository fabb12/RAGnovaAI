import os
import platform
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import win32com.client as win32
from tempfile import TemporaryDirectory
import pythoncom

import shutil

import shutil
import os
import pypandoc
from tempfile import TemporaryDirectory


def convert_doc_to_docx(file_path):
    """Converte un file .doc in .docx usando pypandoc, se disponibile."""
    if not file_path.endswith(".doc"):
        return file_path  # Restituisce il percorso originale se è già un .docx

    # Verifica che il file esista
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Il file {file_path} non esiste.")

    # Usa una directory temporanea per la conversione
    with TemporaryDirectory() as temp_dir:
        converted_path = os.path.join(temp_dir, "converted_document.docx")

        try:
            # Esegue la conversione usando pypandoc
            pypandoc.convert_file(file_path, 'docx', outputfile=converted_path)
            return converted_path  # Restituisce il percorso del file .docx convertito
        except Exception as e:
            raise RuntimeError(f"Errore nella conversione del file {file_path} in .docx: {e}")


def load_document(file_path):
    """Carica un documento PDF, DOC, DOCX o TXT dal percorso specificato."""
    _, extension = os.path.splitext(file_path)

    if extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif extension == '.docx':
        loader = Docx2txtLoader(file_path)
    elif extension == '.doc':
        # Converti il file .doc in .docx e poi carica il .docx
        converted_path = convert_doc_to_docx(file_path)
        loader = Docx2txtLoader(converted_path)
    elif extension == '.txt':
        loader = TextLoader(file_path)
    else:
        raise ValueError("Formato documento non supportato.")

    return loader.load()


def split_text(documents, chunk_size=300, chunk_overlap=100):
    """Divide i documenti in chunk più piccoli."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    return chunks
