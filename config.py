import os
from dotenv import load_dotenv, find_dotenv

# Carica le variabili di ambiente dal file .env
load_dotenv(find_dotenv(), override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
