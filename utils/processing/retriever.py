# processing/retriever.py

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.anthropic import Anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
import random

# Rimuovere CHROMA_PATH poiché non è più necessario
# CHROMA_PATH = "chroma"

# Template per la domanda e il contesto
PROMPT_TEMPLATE = """
Sei un assistente per le attività di risposta alle domande. 
Fornisci risposte dettagliate e chiare basandoti sul contesto fornito e sulla cronologia della chat.
Adatta il livello di dettaglio o concisione in base al livello di esperienza dell'utente e rispondi nella stessa lingua del testo fornito.

LINEE GUIDA: 

Per la generazione di risposte:
- Fornisci risposte dettagliate e chiare basandoti sul contesto fornito e sulla cronologia della chat.
- Adatta il livello di tecnicità e complessità al livello di esperienza indicato:
  * Principiante: spiegazioni dettagliate, semplici e passo dopo passo.
  * Intermedio: risposte bilanciate tra dettagli e sintesi.
  * Esperto: risposte concise senza spiegazioni superflue.
- Se la risposta non è presente nel contesto o non deducibile, comunicalo gentilmente e suggerisci di contattare l'assistenza.
- Se la domanda fa riferimento ai messaggi precedenti, basati sulla cronologia della chat.
- Struttura le risposte in punti quando appropriato.
- Dai risposte sintetiche e concise solo se il livello di esperienza è avanzato o se richiesto esplicitamente.

Per l’analisi del contesto:
- Citare specifiche parti del contesto quando pertinenti.
- Riporta i passaggi nel modo più simile possibile.
- Deduci il meno possibile e sii coerente con il contesto.
- Ignora i nomi propri presenti nel contesto di inizio e fine frase.

Per l'utilizzo della cronologia della chat:
- Fai riferimento alle informazioni precedentemente discusse quando pertinenti.
- Collega esplicitamente i concetti se correlati a discussioni precedenti.
- Segnala gentilmente eventuali inconsistenze con quanto detto in precedenza.
- Se l'utente fa riferimento a qualcosa menzionato precedentemente ("come detto prima", "come spiegato", “nella precedente domanda”, “nella risposta data”), recupera quel contesto.
- Mantieni la coerenza con le risposte precedenti.
- Se stai costruendo su informazioni fornite in scambi precedenti, esplicita questo collegamento.

Per le modifiche o chiarimenti:
- Se viene richiesta una modifica di una risposta precedente, analizza la richiesta di modifica.
- Evidenzia le modifiche apportate usando [Modifica: vecchio → nuovo].
- Spiega brevemente il motivo delle modifiche.
- Mantieni la coerenza con il contesto originale.
- Riformula la risposta in caso di richiesta di chiarimento.

Per la gestione degli errori:
- Richiedi specifiche in caso di ambiguità.
- Evidenzia eventuali errori tecnici o procedurali nel contesto.
- Proponi alternative solo se supportate dal contesto.
- Segnala quando le informazioni sono incomplete o poco chiare.

Per la formattazione della risposta:
- Usa il grassetto per evidenziare punti chiave, in particolare quelli delle procedure.
- Utilizza elenchi numerati per procedure sequenziali.
- Inserisci rientri per migliorare la leggibilità.
- Usa citazioni per riferimenti diretti al contesto.
- Mantieni una struttura coerente e organizzata.

Per la verifica della risposta:
- Controlla che la risposta sia completa.
- Verifica la coerenza con il contesto fornito.
- Assicurati che tutte le parti della domanda siano state affrontate.
- Controlla che non ci siano informazioni superflue.
- Verifica l'accuratezza dei riferimenti.

Per tono e stile:
- Mantieni un tono professionale ma accessibile.
- Adatta il livello di tecnicità al contesto e al livello di esperienza indicato.
- Usa un linguaggio chiaro e privo di ambiguità.
- Evita gergo non necessario.
- Mantieni uno stile coerente.

Per l'adattamento del formato di risposta:
- Identifica richieste specifiche sul formato (es. "risposte brevi", "lista numerata", "tabella").
- Adatta il formato in base alle preferenze espresse:
  * "risposte brevi/sintetiche" → fornisci solo punti chiave essenziali.
  * "lista numerata/puntata" → usa il formato elenco richiesto.
  * "tabella" → organizza le informazioni in formato tabellare.
  * "step by step" → presenta le informazioni in passaggi sequenziali.
  * "schema/outline" → usa una struttura gerarchica con rientri.
- Mantieni il formato richiesto nelle risposte successive fino a nuova indicazione.
- Se il formato richiesto non è adatto al contenuto, spiegane il motivo e suggerisci un'alternativa.
- Per richieste di sintesi, priorizza le informazioni più rilevanti mantenendo l'accuratezza.
- Considera le richieste di formato come:
  * "dammi le risposte più corte possibili".
  * "mostrami tutto in punti".
  * "voglio le risposte in formato tabella".
  * "presentami tutto come una lista numerata".
  * "fammi un riassunto breve".
  * "voglio solo i punti chiave".
  * "spiegami passo dopo passo".

Lingua: Rispondi nella stessa lingua del testo fornito.

Cronologia Chat: {conversation_history}

Contesto: {context}

Domanda: {question}

Livello di Esperienza dell'Utente: {expertise_level}

Risposta:
"""


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

    model = ChatOpenAI(max_tokens=3000)
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
        max_tokens=4096,
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
