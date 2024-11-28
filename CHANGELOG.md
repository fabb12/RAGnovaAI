# Changelog

Questo documento traccia le modifiche apportate al codice per implementare il **semantic chunking** nel progetto esistente. Le modifiche riguardano principalmente l'integrazione del `SemanticChunker` di LangChain per migliorare la suddivisione dei documenti in chunk semantici coerenti.

---

## Versione 1.1.0 - Data: 27/11/2024

### Nuove Funzionalità

- **Implementazione del Semantic Chunking**:
  - **`document_loader.py`**:
    - Aggiunta la funzione `split_text` che utilizza il `SemanticChunker` per suddividere i documenti in chunk basati sulla similarità semantica tra le frasi.
    - Importate le classi e funzioni necessarie:
      ```python
      from langchain_experimental.text_splitter import SemanticChunker
      from langchain.embeddings import OpenAIEmbeddings
      from langchain.schema import Document
      ```
    - La funzione `split_text` ora accetta i seguenti parametri:
      - `buffer_size`
      - `breakpoint_type`
      - `breakpoint_amount`
      - `number_of_chunks`
      - `min_chunk_size`
      - `sentence_split_regex`

- **Aggiornamento dell'Interfaccia Grafica**:
  - **`document_interface.py`**:
    - Rimossi i controlli per `chunk_size` e `chunk_overlap` poiché non sono più utilizzati nel semantic chunking.
    - Aggiunti nuovi controlli per impostare i parametri del `SemanticChunker`:
      - `buffer_size`
      - `breakpoint_type`
      - `breakpoint_amount`
      - `min_chunk_size`
      - `number_of_chunks`
    - Esempio di codice aggiornato per la sezione dei parametri:
      ```python
      # Imposta Parametri di Chunking Semantico
      buffer_size = st.number_input("Buffer Size", min_value=1, max_value=10, value=1, step=1)
      breakpoint_type = st.selectbox("Tipo di Breakpoint Threshold", options=["percentile", "standard_deviation", "interquartile", "gradient"], index=0)
      breakpoint_amount = st.number_input("Breakpoint Threshold Amount", min_value=0.0, max_value=100.0, value=90.0, step=1.0)
      min_chunk_size = st.number_input("Dimensione minima del chunk (caratteri)", min_value=1, max_value=10000, value=500, step=100)
      number_of_chunks = st.number_input("Numero di chunk desiderati (opzionale)", min_value=0, max_value=100, value=0, step=1)
      if number_of_chunks == 0:
          number_of_chunks = None
      ```

- **Aggiornamento del Gestore dei Documenti**:
  - **`document_manager.py`**:
    - Modificato il metodo `add_local_document` per accettare i nuovi parametri del semantic chunking.
    - Esempio di codice aggiornato:
      ```python
      def add_local_document(
          self,
          file_path,
          buffer_size=1,
          breakpoint_type="percentile",
          breakpoint_amount=90,
          number_of_chunks=None,
          min_chunk_size=None
      ):
          # Codice esistente...
          chunks = split_text(
              data,
              buffer_size=buffer_size,
              breakpoint_type=breakpoint_type,
              breakpoint_amount=breakpoint_amount,
              number_of_chunks=number_of_chunks,
              min_chunk_size=min_chunk_size
          )
          # Codice esistente...
      ```

### Modifiche

- **Rimozione dei Parametri Obsoleti**:
  - **`document_loader.py`**:
    - Rimossi `chunk_size` e `chunk_overlap` dalla funzione `split_text` poiché non sono utilizzati dal `SemanticChunker`.
  - **`document_interface.py`**:
    - Rimossi i controlli dell'interfaccia grafica per `chunk_size` e `chunk_overlap`.
  - **`document_manager.py`**:
    - Eliminati i riferimenti a `chunk_size` e `chunk_overlap` nelle chiamate alle funzioni.

- **Aggiornamento della Documentazione del Codice**:
  - Aggiunti commenti esplicativi sulle funzioni e sui parametri utilizzati nel semantic chunking.
  - Fornite spiegazioni dettagliate sui nuovi parametri e sul loro impatto nel processo di suddivisione dei documenti.

### Correzioni di Bug

- **Gestione dell'Errore nel `SemanticChunker`**:
  - Risolto l'errore `SemanticChunker.__init__() got an unexpected keyword argument 'chunk_size'` rimuovendo i parametri non supportati dal costruttore.
  - Modificato il codice per passare i parametri corretti ai metodi appropriati.

### Miglioramenti

- **Ottimizzazione delle Prestazioni**:
  - Implementato un controllo per impostare `number_of_chunks` a `None` se l'utente non specifica un valore, evitando comportamenti imprevisti.
  - Aggiunta la possibilità di specificare una dimensione minima per i chunk tramite `min_chunk_size` per garantire chunk di dimensioni adeguate.

- **Esperienza Utente Migliorata**:
  - Fornite spiegazioni dettagliate nell'interfaccia grafica per aiutare gli utenti a comprendere e utilizzare efficacemente i nuovi parametri.
  - Aggiornata la documentazione e i tooltip nell'interfaccia per riflettere le modifiche apportate.

---

## Versione 1.0.0 - Data: 26/11/2024

### Funzionalità Iniziali

- Implementazione iniziale dell'applicazione con supporto per:

  - Caricamento di documenti in vari formati (PDF, DOCX, TXT, CSV).
  - Suddivisione dei documenti in chunk basati su caratteri con parametri `chunk_size` e `chunk_overlap`.
  - Creazione di embeddings con OpenAI e salvataggio nel vector store ChromaDB.
  - Interfaccia grafica con Streamlit per la gestione dei documenti e l'interrogazione del sistema.

---

