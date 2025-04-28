"""
File: retriever_deepseek.py

Implementa una pipeline di retrieval basata su Deepseek locale.
"""

import os
import re
import streamlit as st
import requests
import networkx as nx
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings  # Modifica qui: sostituzione di langchain_ollama
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

OLLAMA_URL = "http://localhost:11434/api/generate"
GENERATIVE_MODEL = "deepseek-r1:7b"
EMBEDDINGS_MODEL = "nomic-embed-text:latest"

def build_knowledge_graph(docs):
    G = nx.Graph()
    for doc in docs:
        entities = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', doc.page_content)
        if len(entities) > 1:
            for i in range(len(entities) - 1):
                G.add_edge(entities[i], entities[i + 1])
    return G

def retrieve_from_graph(query, G, top_k=5):
    query_words = query.lower().split()
    matched_nodes = [node for node in G.nodes if any(word in node.lower() for word in query_words)]
    if matched_nodes:
        related_nodes = []
        for node in matched_nodes:
            related_nodes.extend(list(G.neighbors(node)))
        return related_nodes[:top_k]
    return []

def process_documents(uploaded_files):
    if st.session_state.get("documents_loaded", False):
        return
    documents = []
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    for file in uploaded_files:
        file_path = os.path.join(temp_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        try:
            if file.name.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file.name.lower().endswith(".docx"):
                loader = Docx2txtLoader(file_path)
            elif file.name.lower().endswith(".txt"):
                loader = TextLoader(file_path)
            else:
                continue
            loaded_docs = loader.load()
            documents.extend(loaded_docs)
        except Exception as e:
            st.error(f"Errore nel processing di {file.name}: {str(e)}")
        finally:
            os.remove(file_path)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separator="\n")
    texts = text_splitter.split_documents(documents)
    text_contents = [doc.page_content for doc in texts]
    # Utilizzo di HuggingFaceEmbeddings al posto di OllamaEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    vector_store = FAISS.from_documents(texts, embeddings)
    retrieval_pipeline = {
        "ensemble": vector_store.as_retriever(search_kwargs={"k": 5}),
        "texts": text_contents,
        "knowledge_graph": build_knowledge_graph(texts)
    }
    st.session_state.retrieval_pipeline = retrieval_pipeline
    st.session_state.documents_loaded = True

def expand_query(query):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": GENERATIVE_MODEL,
            "prompt": f"Generate a hypothetical answer to: {query}",
            "stream": False
        }).json()
        expanded = response.get("response", "")
        return f"{query}\n{expanded}"
    except Exception as e:
        st.error(f"Query expansion failed: {str(e)}")
        return query

def retrieve_documents_deepseek(query, chat_history=""):
    if st.session_state.get("enable_hyde", False):
        expanded_query = expand_query(query)
    else:
        expanded_query = query
    ensemble_retriever = st.session_state.retrieval_pipeline.get("ensemble")
    docs = ensemble_retriever.get_relevant_documents(expanded_query)
    if st.session_state.get("enable_graph_rag", False):
        G = st.session_state.retrieval_pipeline.get("knowledge_graph")
        graph_nodes = retrieve_from_graph(query, G)
        graph_docs = [Document(page_content=node) for node in graph_nodes]
        docs = graph_docs + docs
    max_contexts = st.session_state.get("max_contexts", 3)
    return docs[:max_contexts]

def query_rag_with_deepseek(query_text, vector_store, expertise_level="expert"):
    """
    Esegue una query utilizzando la pipeline Deepseek locale.
    """
    docs = retrieve_documents_deepseek(query_text, chat_history="")
    if not docs:
        return "Non ci sono risultati pertinenti per la tua domanda.", []
    answer = "\n\n".join([doc.page_content for doc in docs])
    references = []
    for doc in docs:
        ref = {
            "file_name": doc.metadata.get("file_name", "Documento sconosciuto"),
            "file_path": doc.metadata.get("file_path", "Percorso sconosciuto"),
            "source_url": doc.metadata.get("source_url", None),
        }
        references.append(ref)
    return answer, references
