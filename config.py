import os
from dotenv import load_dotenv, find_dotenv

# Carica le variabili di ambiente dal file .env
load_dotenv(find_dotenv(), override=True)
API_KEY = os.getenv("OPENAI_API_KEY")
