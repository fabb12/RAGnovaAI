# utils/document_loader.py
import os
import pypandoc
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_document(file_path):
    """Carica un documento PDF, DOC, DOCX o TXT dal percorso specificato."""
    _, extension = os.path.splitext(file_path)
    if extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif extension == '.docx':
        loader = Docx2txtLoader(file_path)
    elif extension == '.doc':
        # Converti il file .doc in .docx temporaneamente
        converted_path = file_path + ".converted.docx"
        pypandoc.convert_file(file_path, 'docx', outputfile=converted_path)
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
