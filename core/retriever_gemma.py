# core/retriever_gemma.py

import requests
from langchain.prompts import ChatPromptTemplate
from core.retriever import load_prompt_from_file

# Carica il template di prompt
PROMPT_TEMPLATE = load_prompt_from_file()

# Configurazione Ollama
# Assicurati che OLLAMA_HOST (es. "http://127.0.0.1:11435") sia settato come env var
OLLAMA_HOST = "http://127.0.0.1:11436"
OLLAMA_URL = f"{OLLAMA_HOST}/generate"
GEMMA_MODEL_NAME = "gemma3:latest"  # dal `ollama list`

def _call_ollama(prompt: str) -> str:
    """
    Invia il prompt a Ollama e ritorna la risposta generata.
    """
    payload = {
        "model": GEMMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        # Mostra dettagli dell’errore Ollama
        raise RuntimeError(f"Ollama API Error {response.status_code}: {response.text}") from e

    data = response.json()
    # Ollama restituisce le risposte in 'choices': [{'text': ...}, ...]
    if isinstance(data, dict) and "choices" in data and data["choices"]:
        return data["choices"][0].get("text", "").strip()
    # Fallback a campo 'response' se presente
    return data.get("response", "").strip()

def query_rag_with_gemma(query_text, vector_store, expertise_level="expert"):
    """
    Esegue una query RAG utilizzando Gemma locale via Ollama.
    1) Recupero semantico dal vector_store.
    2) Costruzione del prompt con contesto e domanda.
    3) Invio del prompt a Ollama e ottenimento della generazione.
    4) Raccolta dei riferimenti dei documenti.
    """
    # 1) Recupero semantico
    results = vector_store.similarity_search_with_score(query_text, k=5)
    if not results:
        return "Non ci sono risultati pertinenti per la tua domanda.", []

    # 2) Costruzione del contesto
    context = "\n\n---\n\n".join([doc.page_content for doc, _ in results])

    # 3) Preparazione prompt
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context,
        question=query_text,
        expertise_level=expertise_level,
        conversation_history=""
    )

    # 4) Chiamata a Gemma via Ollama
    generated_text = _call_ollama(prompt)

    # 5) Riferimenti
    references = [
        {
            "file_name": doc.metadata.get("file_name", "Documento sconosciuto"),
            "file_path": doc.metadata.get("file_path", None),
            "source_url": doc.metadata.get("source_url", None),
        }
        for doc, _ in results
    ]

    # Rimuovi il prompt dal testo generato, se presente
    if generated_text.startswith(prompt):
        answer = generated_text[len(prompt):].strip()
    else:
        answer = generated_text

    return answer, references
