from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
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


def load_document(file_path):
    """
    Carica un documento PDF, DOCX o TXT dal percorso specificato.
    Restituisce None se il formato non è supportato.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()  # Normalizza l'estensione per evitare problemi con maiuscole/minuscole

    if extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif extension == '.docx':
        loader = Docx2txtLoader(file_path)
    elif extension == '.txt':
        loader = TextLoader(file_path)
    else:
        # Se il formato non è supportato, non fare nulla
        return None

    # Carica il contenuto del documento
    return loader.load()


def split_text(documents, chunk_size=300, chunk_overlap=100):
    """Divide i documenti in chunk più piccoli."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    return chunks
