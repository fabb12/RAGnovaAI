# utils/retriever.py

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Rispondi alla seguente domanda in modo dettagliato, basandoti solo sul contesto fornito. Fornisci una risposta completa e approfondita:
{context}
-
Risposta alla domanda: {question}
"""

def query_rag(query_text):
    """Esegue una query sul database Chroma e ottiene una risposta arricchita dal contesto."""
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Cerca i documenti rilevanti
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "Non ci sono risultati pertinenti per la tua domanda."

    # Costruisci il contesto per la query
    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(context=context_text, question=query_text)

    # Modello di linguaggio con parametro max_tokens aumentato
    model = ChatOpenAI(max_tokens=3000)  # Aumenta max_tokens per risposte più lunghe
    response_text = model.predict(prompt)
    return response_text
