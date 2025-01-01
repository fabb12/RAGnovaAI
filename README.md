
# RAGnova ( MFHelpDeskAI )

**RAGnova** è un’applicazione **Streamlit** che fornisce un sistema di Q&A (Question & Answer) basato sull’integrazione di modelli LLM (Large Language Models) e **Retrieval-Augmented Generation** (RAG).  
Questo sistema utilizza **OpenAI** (modello GPT) e/o **Anthropic** (modello Claude) per rispondere a domande basate su documentazione interna, caricata dall’utente nella “Knowledge Base”.

## Caratteristiche Principali
1. **Login Utente e Gestione Sessioni**: L’app richiede il login, gestisce i token di sessione e mantiene la cronologia delle conversazioni personalizzata per utente.
2. **Knowledge Base Personale**: Ogni utente può creare e gestire più Knowledge Base, caricando documenti in vari formati (PDF, DOCX, TXT, ecc.) o contenuti web (URL).
3. **Chunking Semantico**: I documenti vengono indicizzati e suddivisi in “chunk” con criteri semantici, facilitando l’accuratezza delle risposte in fase di retrieval.
4. **Scelta Modello LLM**: Supporto a GPT (OpenAI) e Claude (Anthropic), selezionabili dal pannello laterale di Streamlit.
5. **Riferimenti alle Fonti**: Le risposte generate includono i riferimenti (link o percorsi file) ai documenti di provenienza.

---

## Requisiti 

- **Python 3.9+**  
- **pip** o **conda** per gestire i pacchetti.  
- **Streamlit** installato (versioni testate: 1.24+).  
- Chiavi API per **OpenAI** e/o **Anthropic** (selezionabili da `.env`):
  - `OPENAI_API_KEY`  
  - `ANTHROPIC_API_KEY`

### File `.env`
Il progetto carica le variabili da un file `.env`. Qui è possibile specificare le chiavi API e il modello di default:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
DEFAULT_MODEL=GPT (OpenAI)
```
Sostituire i valori con le proprie chiavi valide e, se necessario, cambiare `DEFAULT_MODEL` in `"Claude (Anthropic)"`.

---

## Struttura del Progetto

```plaintext
MFHelpDeskAI/
├─ app.py                  # Entry point: Avvio dell'app Streamlit
├─ config.py               # Gestione variabili di ambiente e chiavi API
├─ database.py             # Inizializzazione/Caricamento di Chroma DB
├─ document_interface.py   # Interfaccia Streamlit per gestione documenti (upload, rimozione, visualizzazione)
├─ document_manager.py     # Logica per manipolare i documenti, chunking, salvataggio in DB
├─ ui_components.py        # Funzioni per personalizzare la UI (CSS ecc.)
├─ utils/
│  ├─ formatting/
│  │  └─ formatter.py      # Funzioni per formattare la risposta e mostrarla in Streamlit con i riferimenti
│  ├─ loaders/
│  │  ├─ document_loader.py  # Caricamento di PDF, Docx, Testi, CSV, Web
│  │  ├─ excel_manager.py    # Caricamento e preview di file Excel
│  │  └─ image_manager.py    # Esempio di gestione immagini con OCR (non sempre necessario)
│  └─ processing/
│     ├─ embeddings.py       # Creazione e gestione degli embeddings su Chroma
│     └─ retriever.py        # Funzioni per interrogare il Vector Store + prompt di Query con GPT/Claude
├─ style.css               # Stili personalizzati CSS per Streamlit
├─ users.json              # File di esempio per credenziali utente (username:password)
├─ prompt_template.txt     # Prompt template usato per la RAG
└─ README.md               # Il file che stai leggendo
```

### Descrizione dei File Principali

1. **`app.py`**  
   - È il cuore dell’applicazione Streamlit: gestisce il login utente, la navigazione tra la pagina delle domande e la pagina di gestione documenti, il caricamento e salvataggio della cronologia.

2. **`config.py`**  
   - Carica le variabili d’ambiente da `.env` e fornisce costanti come `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e `DEFAULT_MODEL`.

3. **`database.py`**  
   - Fornisce la funzione `load_or_create_chroma_db` per inizializzare o caricare un Vector Store basato su [Chroma](https://docs.trychroma.com/).

4. **`document_interface.py`** e **`document_manager.py`**  
   - Gestione completa dei documenti caricati: salvataggio fisico, estrazione testo/metadata, suddivisione in chunk, indexing nel Vector Store.
   - `document_interface.py` si occupa della parte di interfaccia Streamlit.  
   - `document_manager.py` si occupa della logica per aggiungere, eliminare e recuperare i documenti dal database Chroma.

5. **`ui_components.py`**  
   - Applica lo stile personalizzato `style.css` e può contenere altri componenti UI.

6. **`utils/formatting/formatter.py`**  
   - Formattazione della risposta generata dal modello (testo finale, link ai documenti di riferimento, pulsanti Apri e Scarica).

7. **`utils/loaders/document_loader.py`**  
   - Caricamento (loader) per diversi formati (PDF, DOCX, TXT, CSV). Gestisce anche la conversione .doc in .docx, se necessario.

8. **`utils/processing/embeddings.py`**  
   - Funzione di creazione o caricamento di un Vector Store in Chroma, con embeddings OpenAI.

9. **`utils/processing/retriever.py`**  
   - Contiene le funzioni `query_rag_with_gpt` e `query_rag_with_cloud` che:
     - Eseguono la ricerca di contesto rilevante nel Vector Store  
     - Creano il prompt completo  
     - Invocano il modello (OpenAI GPT o Anthropic Claude)  
     - Restituiscono la risposta e i riferimenti.

10. **`style.css`**  
    - File di stile personalizzato per abbellire l’app Streamlit.

11. **`users.json`**  
    - File JSON di esempio per la gestione degli utenti (username/password).  
    - **Nota**: in un ambiente di produzione, sarebbe opportuno usare un database o un sistema di autenticazione più sicuro.

---

## Installazione

1. **Clona il repository**:
   ```bash
   git clone https://github.com/fabb12/MFHelpDeskAI.git
   cd MFHelpDeskAI
   ```

2. **Crea un ambiente virtuale** (consigliato):
   ```bash
   python -m venv venv
   source venv/bin/activate   # per Mac/Linux
   # oppure:
   .\venv\Scripts\activate    # per Windows
   ```

3. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```
   Se non presente un file `requirements.txt`, puoi generarlo con:
   ```bash
   pip freeze > requirements.txt
   ```

4. **Configura le chiavi API**:  
   - Rinomina (oppure crea) il file `.env` e inserisci le tue chiavi:
     ```bash
     OPENAI_API_KEY=sk-...
     ANTHROPIC_API_KEY=...
     DEFAULT_MODEL=GPT (OpenAI)
     ```
   - Se non usi Anthropic, puoi lasciare vuota la chiave `ANTHROPIC_API_KEY` (o viceversa).

5. **Avvia l’applicazione**:
   ```bash
   streamlit run app.py
   ```
   Lo script **`app.py`** avvierà il server Streamlit. Apri il browser all’indirizzo locale mostrato in console, di solito [http://localhost:8501](http://localhost:8501).

---

## Utilizzo

1. **Login**  
   - La pagina iniziale richiede Username e Password (da `users.json` se stai usando l’esempio di default).  
   - Inserisci le credenziali e clicca “Login”.

2. **Seleziona / Crea Knowledge Base**  
   - Dalla sidebar a sinistra, puoi selezionare una KB esistente oppure crearne di nuove dalla sezione *Gestione Documenti*.

3. **Carica Documenti**  
   - Nella sezione *Gestione Documenti*, puoi caricare file PDF, Docx, TXT, CSV.  
   - Oppure inserire un URL per “scansionare” e salvare il contenuto web.

4. **Domande e Risposte**  
   - Passa alla sezione “Domande”.  
   - Digita la tua domanda o incolla un URL. Se è un URL, verrà caricato direttamente nella KB.  
   - Altrimenti, se la KB è popolata, riceverai una risposta basata sui documenti caricati.  
   - Verranno mostrati anche i riferimenti (link a file o contenuti web).

5. **Storia delle Conversazioni**  
   - Sulla sidebar, trovi la cronologia delle ultime domande e risposte.  
   - Cliccando sul tasto “Usa”, puoi reimpostare quella domanda nel campo di input per riutilizzarla.

6. **Logout**  
   - Nella parte bassa della sidebar si trova il pulsante di Logout, che invalida il token di sessione.

---

## Note Aggiuntive

- **Persistenza**: Le Knowledge Base vengono salvate in cartelle `chroma_username_kbname`. Ogni utente (username) può avere più KB.  
- **Prompt Personalizzabile**: Il file `prompt_template.txt` definisce il formato del prompt RAG. Puoi modificarlo per personalizzare lo stile delle risposte.  
- **Gestione Sicurezza**: Per progetti in produzione, si consiglia di adottare un approccio più robusto per la gestione delle credenziali (ad esempio, un database protetto, OAuth, ecc.).

## Autore e Informazioni

- Sviluppato da FFA.
- Per supporto, consulta la documentazione o contatta l'autore.

