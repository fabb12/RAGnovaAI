from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
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


def load_document(file_path_or_url):
    """
    Carica un documento PDF, DOCX, TXT, CSV o un sito web.
    - file_path_or_url può essere un percorso locale o un URL.
    Restituisce None se il formato non è supportato.
    """
    # Controlla se è un URL o un file locale
    if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
        # Caricamento da sito web
        try:
            loader = WebBaseLoader(web_paths=[file_path_or_url])
            return loader.load()
        except Exception as e:
            raise RuntimeError(f"Errore nel caricamento del sito web {file_path_or_url}: {e}")
    else:
        # Estrazione dell'estensione del file
        _, extension = os.path.splitext(file_path_or_url)
        extension = extension.lower()  # Normalizza l'estensione

        if extension == '.pdf':
            loader = PyPDFLoader(file_path_or_url)
        elif extension == '.docx':
            loader = Docx2txtLoader(file_path_or_url)
        elif extension == '.txt':
            loader = TextLoader(file_path_or_url)
        elif extension == '.csv':
            loader = CSVLoader(file_path=file_path_or_url)
        elif extension == '.doc':
            # Converte .doc in .docx prima di caricarlo
            file_path_or_url = convert_doc_to_docx(file_path_or_url)
            loader = Docx2txtLoader(file_path_or_url)
        else:
            # Se il formato non è supportato
            return None

        try:
            # Carica il contenuto del documento
            return loader.load()
        except Exception as e:
            raise RuntimeError(f"Errore nel caricamento del file {file_path_or_url}: {e}")


def split_text(documents, chunk_size=300, chunk_overlap=100):
    """Divide i documenti in chunk più piccoli."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    return chunks
