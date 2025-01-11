# RAGnova (MFHelpDeskAI)

**RAGnova** è un’applicazione **Streamlit** che fornisce un sistema di Q&A (Question & Answer) basato sull’integrazione di modelli LLM (Large Language Models) e **Retrieval-Augmented Generation** (RAG).  
Questo sistema utilizza **OpenAI** (modello GPT) e/o **Anthropic** (modello Claude) per rispondere a domande basate su documentazione interna, caricata dall’utente nella “Knowledge Base”.

---

## Caratteristiche Principali

1. **Login Utente e Gestione Sessioni**  
   - L’app richiede il login, gestisce i token di sessione e mantiene la cronologia delle conversazioni personalizzata per ciascun utente.  

2. **Knowledge Base Personale**  
   - Ogni utente può creare e gestire più Knowledge Base, caricando documenti in vari formati (PDF, DOCX, TXT, CSV, ecc.) o contenuti web (URL).  

3. **Chunking Semantico**  
   - I documenti vengono indicizzati e suddivisi in “chunk” con criteri semantici, migliorando l’accuratezza delle risposte in fase di retrieval.  

4. **Scelta Modello LLM**  
   - Supporto a GPT (OpenAI) e Claude (Anthropic), selezionabili dal pannello laterale di Streamlit.  

5. **Riferimenti alle Fonti**  
   - Le risposte includono i riferimenti (link o percorsi file) ai documenti da cui è stata estratta l’informazione.

---

## Requisiti

- **Python 3.9+**  
- **Streamlit** (versione testata 1.24+)  
- **Chiavi API** per **OpenAI** o **Anthropic** (facoltative a seconda dei modelli che vuoi utilizzare):
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`

### File `.env`
Il progetto carica le variabili d’ambiente dal file `.env`. Puoi specificare le chiavi API e il modello di default. Esempio:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
DEFAULT_MODEL=GPT (OpenAI)
```

Sostituisci i valori con le tue chiavi valide e, se necessario, imposta `DEFAULT_MODEL` su `"Claude (Anthropic)"`.

---

## Architettura usata

Il progetto ha una struttura **a due livelli**:

1. **Core Logic e Utilities**: Qui risiede la logica principale, la gestione dei documenti, il retrieval, il caricamento e la persistenza (ChromaDB), oltre a utility condivise.  
2. **Presentation/UI**: Codice specifico di Streamlit che interagisce con l’utente (pagine, form, caricamento file, layout).

### Esempio di Struttura di Cartelle

```plaintext
MFHelpDeskAI/
├─ app.py                           # Punto d’ingresso: avvio dell'app Streamlit
├─ config.py                        # Configurazione e variabili d'ambiente
├─ core/                            # Logica principale (gestione DB, retrieval, chunking)
│  ├─ database.py                   # Gestione ChromaDB
│  ├─ document_manager.py           # Logica per documenti (aggiunta, eliminazione, chunking)
│  ├─ embeddings.py                 # Creazione e gestione degli embeddings
│  ├─ retriever.py                  # Funzioni per query RAG, GPT/Claude
│  ├─ formatter.py                  # Funzioni per formattare le risposte
├─ ui/                              # Interfaccia Streamlit (UI, form, layout)
│  ├─ ui_components.py              # Componenti UI (layout, pulsanti, sidebar)
│  └─ document_interface.py         # Interfaccia dedicata alla gestione documenti
├─ utils/                           # Funzioni accessorie e condivise
│  ├─ document_loader.py            # Caricamento di file PDF, Docx, TXT, CSV, Web
│  ├─ excel_manager.py              # Gestione file Excel
│  └─ image_manager.py              # Estrazione testo da immagini (OCR) [da completare]
├─ style.css                        # Stili CSS personalizzati
├─ prompt_template.txt              # Template per il prompt RAG
├─ users.json                       # Credenziali (username:password) per test
├─ requirements.txt                 # File delle dipendenze
└─ README.md                        # Documentazione principale
```

---

## Installazione

1. **Clona il repository**  
   ```bash
   git clone https://github.com/fabb12/MFHelpDeskAI.git
   cd MFHelpDeskAI
   ```

2. **Crea un ambiente virtuale** (opzionale ma consigliato)  
   ```bash
   python -m venv venv
   source venv/bin/activate       # Mac/Linux
   # oppure:
   .\venv\Scripts\activate        # Windows
   ```

3. **Installa le dipendenze**  
   ```bash
   pip install -r requirements.txt
   ```
   Se `requirements.txt` non fosse presente, puoi generarlo con:  
   ```bash
   pip freeze > requirements.txt
   ```

4. **Configura le chiavi API** (se necessario)  
   - Rinomina o crea il file `.env` e imposta le tue chiavi:
     ```bash
     OPENAI_API_KEY=sk-...
     ANTHROPIC_API_KEY=...
     DEFAULT_MODEL=GPT (OpenAI)
     ```

5. **Avvia l’applicazione**  
   ```bash
   streamlit run app.py
   ```
   Apri il browser sull’indirizzo locale riportato in console, tipicamente [http://localhost:8501](http://localhost:8501).

---

## Utilizzo

1. **Login**  
   - Nella pagina iniziale, inserisci le credenziali 

2. **Gestione Knowledge Base**  
   - Dalla sidebar, puoi selezionare o creare una Knowledge Base.  
   - Passa alla sezione *Gestione Documenti* per caricare file (PDF, DOCX, TXT, CSV) o URL.

3. **Domande e Risposte**  
   - Passa alla sezione “Domande”.  
   - Digita la tua domanda e premi invio. Se è un URL, verrà automaticamente caricato nella KB.  
   - Riceverai una risposta generata dai modelli GPT o Claude, insieme ai riferimenti alle fonti.

4. **Storico delle Conversazioni**  
   - Nella sidebar, puoi consultare e riutilizzare le domande precedenti.

5. **Logout**  
   - Puoi disconnetterti dal pulsante di logout nella sidebar.

---

## Note Aggiuntive

- **Persistenza**: Le Knowledge Base vengono salvate in cartelle come `chroma_username_kbname`; ogni utente (username) gestisce le proprie.  
- **Prompt Personalizzabile**: Il file `prompt_template.txt` definisce la struttura del prompt RAG. Modificalo in base alle tue necessità.  
---

## Autore

- Sviluppato da FFA.  
