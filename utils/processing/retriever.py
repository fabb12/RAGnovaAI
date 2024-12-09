# processing/retriever.py

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.anthropic import Anthropic
from anthropic import Anthropic
import os

def load_prompt_from_file(file_path="prompt_template.txt"):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


PROMPT_TEMPLATE = load_prompt_from_file()

def query_rag_with_gpt(query_text, vector_store, expertise_level="expert"):
    """
    Esegue una query sul vector_store fornito e restituisce una risposta arricchita dal contesto.
    Restituisce la risposta generata e un elenco di riferimenti ai documenti pertinenti.
    """
    results = vector_store.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "Non ci sono risultati pertinenti per la tua domanda.", []

    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        context=context_text,
        question=query_text,
        expertise_level=expertise_level,
        conversation_history=""
    )

    model = ChatOpenAI(max_tokens=5000)
    response_text = model.predict(prompt)

    references = [
        {
            "file_name": doc.metadata.get("file_name", "Documento sconosciuto"),
            "file_path": doc.metadata.get("file_path", "Percorso sconosciuto"),
        }
        for doc, _ in results
    ]

    return response_text, references

def query_rag_with_cloud(query_text, vector_store, expertise_level="expert"):
    """
    Esegue una query sul vector_store fornito e restituisce una risposta arricchita dal contesto
    utilizzando l'SDK di Anthropic con il modello specificato.
    """
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("La chiave API di Anthropic non è impostata. Verifica il file `.env`.")

    results = vector_store.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "Non ci sono risultati pertinenti per la tua domanda.", [], 0, 0

    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        context=context_text,
        question=query_text,
        expertise_level=expertise_level,
        conversation_history=""
    )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        temperature=0.7,
        system=PROMPT_TEMPLATE,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    result_text = message.content[0].text
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    references = [
        {
            "file_name": doc.metadata.get("file_name", "Documento sconosciuto"),
            "file_path": doc.metadata.get("file_path", "Percorso sconosciuto"),
        }
        for doc, _ in results
    ]

    return result_text, references, input_tokens, output_tokens
