# utils/retriever.py

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Percorso per il database Chroma
CHROMA_PATH = "chroma"

# Template per la domanda e il contesto
PROMPT_TEMPLATE = """
Rispondi alla seguente domanda in modo dettagliato, basandoti solo sul contesto fornito. Fornisci una risposta completa e approfondita:
{context}
-
Risposta alla domanda: {question}
"""

def query_rag(query_text):
    """
    Esegue una query sul database Chroma e ottiene una risposta arricchita dal contesto.
    Restituisce la risposta generata e un elenco di documenti di riferimento univoci solo se pertinenti.
    """
    # Inizializza ChromaDB con la funzione di embedding
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Esegue la ricerca di similarità
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        # Nessun documento pertinente, quindi ritorna solo la risposta senza riferimenti
        return "Non ci sono risultati pertinenti per la tua domanda.", []

    # Costruisci il contesto per il prompt
    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Inizializza il modello ChatOpenAI con più tokens per risposte più lunghe
    model = ChatOpenAI(max_tokens=3000)
    response_text = model.predict(prompt)

    # Recupera i nomi dei documenti di riferimento utilizzati per il contesto, evitando duplicati
    references = [doc.metadata.get("file_name", "Documento sconosciuto") for doc, _ in results]
    unique_references = list(set(references))  # Rimuove duplicati

    # Ritorna la risposta e i riferimenti unici
    return response_text, unique_references
