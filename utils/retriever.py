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
You are a support assistant, helping users by answering questions based on provided information and following these steps:

1. Break down the question into simpler sub-questions if needed, to address each part accurately.
2. For each sub-question:
   a. Identify the most relevant information from the context, taking into account conversation history if available.
3. Use the selected information to draft a response, adjusting the level of detail or conciseness based on the user’s expertise:
   - Provide detailed explanations for beginners.
   - Provide concise answers without explanations for experts.
4. Remove redundant content from your response draft.
5. Finalize your response to maximize clarity and relevance.
6. Respond only with your final answer—avoid any extra explanations of your thought process.

If the information needed to answer the question is not present in the context, respond with 'I don't know' in the language of the user's question"

Context:
{context}

Conversation History:
{conversation_history}

User's Question:
{question}

User's Expertise Level: {expertise_level}

Note: Answer in the language of the user’s question.
""".replace("{conversation_history}", "{conversation_history:}")


# Frasi indicative di risposte fuori contesto
OUT_OF_CONTEXT_RESPONSES = [
    "Non lo so",
]

def query_rag_with_gpt(query_text, expertise_level="expert"):
    """
    Executes a query on the Chroma database and retrieves a context-enriched response.
    Returns the generated response and a list of relevant document references with paths.
    """
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db.similarity_search_with_relevance_scores(query_text, k=3)
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

    if any(phrase.lower() in response_text.lower() for phrase in OUT_OF_CONTEXT_RESPONSES):
        return response_text, []

    references = [
        {
            "file_name": doc.metadata.get("file_name", "Documento sconosciuto"),
            "file_path": doc.metadata.get("file_path", "Percorso sconosciuto"),
        }
        for doc, _ in results
    ]

    return response_text, references


def query_rag_with_cloud(query_text, expertise_level="expert"):
    """
    Executes a query on the Chroma database and retrieves a context-enhanced response
    using Anthropic's SDK with the specified model.
    """
    # Get the API key from the `.env` file or environment variable
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is not set. Check the `.env` file.")

    # Initialize Chroma database for context
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search for relevant documents for context
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        return "No relevant results found for your question.", [], 0, 0

    # Prepare the context text
    context_text = "\n\n- -\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # Add conversation_history with a default empty value
    prompt = prompt_template.format(
        context=context_text,
        question=query_text,
        expertise_level=expertise_level,
        conversation_history=""
    )

    # Configure the Anthropic client
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

    # Extract the generated response and token usage
    result_text = message.content[0].text
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    # Check if the response is out of context
    if any(phrase.lower() in result_text.lower() for phrase in OUT_OF_CONTEXT_RESPONSES):
        return result_text, [], input_tokens, output_tokens

    # Retrieve document references with paths
    references = [
        {
            "file_name": doc.metadata.get("file_name", "Unknown Document"),
            "file_path": doc.metadata.get("file_path", "Unknown Path"),
        }
        for doc, _ in results
    ]

    return result_text, references, input_tokens, output_tokens
