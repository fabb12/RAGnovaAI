# utils/retriever.py

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os
from langchain_community.llms.anthropic import Anthropic
from anthropic import  HUMAN_PROMPT, AI_PROMPT
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os

# Percorso per il database Chroma
CHROMA_PATH = "chroma"

# Template per la domanda e il contesto
PROMPT_TEMPLATE = """
Rispondi alla seguente domanda in modo dettagliato solo se è pertinente al contesto fornito. 
Se la domanda non è pertinente o se le informazioni non sono nel contesto, rispondi solo: "Non lo so".

Contesto:
{context}
-
Domanda: {question}
"""

# Frasi indicative di risposte fuori contesto
OUT_OF_CONTEXT_RESPONSES = [
    "Non lo so",
]

def query_rag_with_gpt(query_text):
    """
    Esegue una query sul database Chroma e ottiene una risposta arricchita dal contesto.
    Restituisce la risposta generata e un elenco di documenti di riferimento univoci solo se pertinenti.
    """
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "Non ci sono risultati pertinenti per la tua domanda.", []

    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    model = ChatOpenAI(max_tokens=3000)
    response_text = model.predict(prompt)

    if any(phrase.lower() in response_text.lower() for phrase in OUT_OF_CONTEXT_RESPONSES):
        return response_text, []

    references = list({doc.metadata.get("file_name", "Documento sconosciuto") for doc, _ in results})
    return response_text, references




def query_rag_with_cloud(query_text):
    """
    Esegue una query sul database Chroma e ottiene una risposta arricchita dal contesto
    utilizzando direttamente l'SDK di Anthropic con il modello specificato.
    """
    # Ottieni la chiave API dal file `.env` o da una variabile di ambiente
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("La chiave API di Anthropic non è impostata. Verifica il file `.env`.")

    # Inizializza il database Chroma per il contesto
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Ricerca i documenti pertinenti per il contesto
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "Non ci sono risultati pertinenti per la tua domanda.", []

    # Prepara il contesto per il prompt
    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    formatted_prompt = f"Contesto:\n{context_text}\n\nDomanda: {query_text}\n\nAssistant:"

    # Configura il client Anthropic con il modello specifico
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        temperature=0.7,
        system=(
            "Sei un assistente utile che risponde alle domande basandosi sul contesto fornito. "
            "Rispondi in modo conciso e accurato in italiano, basandoti solo sul contesto dato. "
            "Se la risposta non è chiara, rispondi con 'Non lo so'."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": formatted_prompt
                    }
                ]
            }
        ]
    )

    # Estrarre la risposta generata e i token utilizzati
    testo_resultante = message.content[0].text
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    # Verifica se la risposta è fuori contesto
    if any(phrase.lower() in testo_resultante.lower() for phrase in OUT_OF_CONTEXT_RESPONSES):
        return testo_resultante, [], input_tokens, output_tokens

    # Recupera i riferimenti dai documenti
    references = list({doc.metadata.get("file_name", "Documento sconosciuto") for doc, _ in results})
    return testo_resultante, references, input_tokens, output_tokens