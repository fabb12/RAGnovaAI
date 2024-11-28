# Changelog

Questo documento riassume le modifiche apportate per implementare il **semantic chunking** nel progetto.

---

## Versione 1.1.0 - Data: 27/11/2024

### Nuove Funzionalità

- aggiunto caricamento siti web con parametro livello di profondita'

- **Integrazione del Semantic Chunking**:
  - Implementata la funzione `split_text` in `document_loader.py` utilizzando `SemanticChunker` di LangChain.
  - Aggiornati gli import necessari per supportare il semantic chunking.
  - La funzione `split_text` ora accetta parametri specifici per il semantic chunking:
    - `buffer_size`
    - `breakpoint_type`
    - `breakpoint_amount`
    - `number_of_chunks`
    - `min_chunk_size`

- **Aggiornamento dell'Interfaccia Grafica**:
  - In `document_interface.py`, rimossi i controlli per `chunk_size` e `chunk_overlap`.
  - Aggiunti nuovi controlli per impostare i parametri del `SemanticChunker`.

- **Modifiche al Gestore dei Documenti**:
  - In `document_manager.py`, aggiornato il metodo `add_local_document` per accettare i nuovi parametri del semantic chunking.

### Modifiche

- **Rimozione di Parametri Obsoleti**:
  - Eliminati `chunk_size` e `chunk_overlap` dalle funzioni e dall'interfaccia, poiché non utilizzati nel semantic chunking.

- **Aggiornamento della Documentazione**:
  - Aggiunti commenti e spiegazioni sui nuovi parametri e sul loro utilizzo.

### Correzioni di Bug

- **Errore nel `SemanticChunker`**:
  - Risolto l'errore relativo ai parametri non supportati nel costruttore di `SemanticChunker`.

### Miglioramenti

- **Ottimizzazione delle Prestazioni**:
  - Implementato controllo per impostare `number_of_chunks` a `None` se non specificato.

- **Miglioramento dell'Esperienza Utente**:
  - Fornite spiegazioni dettagliate nell'interfaccia per aiutare gli utenti a comprendere i nuovi parametri.

---

## Versione 1.0.0 - Data: 26/11/2024

### Funzionalità Iniziali

- Caricamento di documenti in vari formati (PDF, DOCX, TXT, CSV).
- Suddivisione dei documenti in chunk basati su caratteri.
- Creazione di embeddings con OpenAI e salvataggio in ChromaDB.
- Interfaccia grafica con Streamlit per la gestione dei documenti e le query.

---

# Note

- **Aggiornamento delle Dipendenze**:
  - Assicurarsi di avere l'ultima versione di `langchain` e `langchain_experimental`.

- **Ricostruzione del Vector Store**:
  - Potrebbe essere necessario rigenerare gli embeddings per i documenti esistenti.

- **Consigli d'Uso**:
  - Sperimentare con i nuovi parametri del semantic chunking per ottimizzare i risultati.