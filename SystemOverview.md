# Architettura ad Alto Livello del Sistema HelpDeskRAG

## Sommario
- [Introduzione](#introduzione)  
- [Contesto e Obiettivi](#contesto-e-obiettivi)  
- [Panoramica dell’Architettura](#panoramica-dellarchitettura)  
  - [Flow Diagram](#flow-diagram)
- [Pattern Architetturale: Retrieval-Augmented Generation (RAG)](#pattern-architetturale-retrieval-augmented-generation-rag)
- [Principali Componenti](#principali-componenti)  
  1. [UI & Application Layer (Streamlit)](#1-ui--application-layer-streamlit)  
  2. [Document Interface & Document Manager](#2-document-interface--document-manager)  
  3. [Database e Vector Store (Chroma)](#3-database-e-vector-store-chroma)  
  4. [Utility e Moduli di Supporto](#4-utility-e-moduli-di-supporto)  
- [Flow di una Richiesta di Domanda (RAG Pipeline)](#flow-di-una-richiesta-di-domanda-rag-pipeline)
- [Conclusioni](#conclusioni)

---

## Introduzione
Il sistema **HelpDeskRAG** è un’applicazione basata su Streamlit che permette di caricare, gestire e consultare documenti (in vari formati: PDF, docx, testo, web, ecc.) per fornire risposte intelligenti (*Q&A*) tramite modelli di linguaggio **OpenAI GPT** o **Anthropic Claude**. L’architettura segue un pattern **RAG** (Retrieval-Augmented Generation), che combina l’approccio di *embedding* e *similarity search* con la generazione di risposte in linguaggio naturale.

---

## Contesto e Obiettivi
- **Contesto**: Spesso le aziende hanno un’ampia base di documenti (manuali, PDF, pagine web) che gli utenti devono consultare rapidamente.  
- **Obiettivo**: Fornire uno strumento *user-friendly* in cui l’utente possa porre domande in linguaggio naturale e ottenere risposte pertinenti, corredate da riferimenti ai documenti sorgente.

---

## Panoramica dell’Architettura
Il sistema adotta una struttura **modulare** e **layered**, in cui si distinguono quattro livelli fondamentali:

1. **UI & Application Layer** – L’interfaccia utente sviluppata con Streamlit (file `app.py`).  
2. **Document Layer** – La logica per l’importazione, il caricamento, la gestione e la cancellazione dei documenti (file `document_interface.py`, `document_manager.py`).  
3. **Database & Vector Store Layer** – Gestione dei contenuti indicizzati con *Chroma* (file `database.py`).  
4. **Utility & Processing Layer** – Funzionalità di supporto: formattazione risposte, *embeddings*, *retriever*, caricamento file, ecc. (cartella `utils`).

### Flow Diagram
```mermaid
flowchart LR
    A[Utente] -->|1. Domanda / Upload| B[UI Streamlit (app.py)]
    B -->|2. Chiamate Gestione Documenti| C[DocumentManager / DocumentInterface]
    C -->|3. Aggiunta / Rimozione / Lettura| D[Vector Store (Chroma DB)]
    B -->|4. Query Modelli GPT/Claude| E[Retriever & Embedding]
    E -->|5. Similarity Search| D
    E -->|6. Restituzione Risposta + Riferimenti| B
    B -->|7. Output su UI| A
```

---

## Pattern Architetturale: *Retrieval-Augmented Generation* (RAG)
Il **Retrieval-Augmented Generation** si basa sull’idea di **recuperare** (retrieve) i contenuti pertinenti da una *knowledge base* (indicizzata in un *vector store*) e poi **generare** (generate) una risposta contestualizzata usando un modello di linguaggio di grandi dimensioni.

1. L’utente pone una domanda (*query*).  
2. Il sistema cerca i contenuti più simili o rilevanti nella **knowledge base** (passo “retrieval”).  
3. Il **modello di linguaggio** (GPT o Claude) riceve i testi recuperati come contesto, e genera una risposta più accurata (passo “generation”).  
4. La risposta è poi mostrata con i riferimenti ai documenti sorgente.

---

## Principali Componenti

### 1. UI & Application Layer (Streamlit)
- **File principale**: `app.py`  
- **Funzionalità chiave**:
  - Gestione sessioni degli utenti (login, token di sessione).  
  - Configurazione della pagina (titolo, layout, sidebar).  
  - Permette la **selezione del modello** (GPT/Claude) e la Knowledge Base.  
  - Raccolta della *query* dell’utente, invio al *retriever*, e visualizzazione della risposta formattata.  
  - Struttura a schede (Domande / Gestione Documenti).

### 2. Document Interface & Document Manager
- **File**: `document_interface.py`, `document_manager.py`
- **DocumentInterface**:
  - Espone le funzionalità di caricamento, visualizzazione e rimozione dei documenti.  
  - Gestisce l’upload di più formati (PDF, .docx, .txt, ecc.).  
  - Fornisce metodi per aggiungere documenti web (tramite URL).  
- **DocumentManager**:
  - Si occupa dell’elaborazione vera e propria (lettura con `document_loader`, hashing, suddivisione in chunk, salvataggio nel vector store).  
  - Implementa la *fetch_web_content* (crawler di base) per acquisire contenuti HTML su più *depth level*.  
  - Gestisce l’eliminazione e la deduplicazione (via *file_hash*).

### 3. Database e Vector Store (Chroma)
- **File**: `database.py`
- **Funzionalità**:
  - Utilizza la libreria **Chroma** per costruire e gestire un *vector store* persistente.  
  - Fornisce il metodo `load_or_create_chroma_db()` che, dato un nome KB (`username_kbName`), crea o carica la Knowledge Base esistente.
  - Ogni chunk è associato a *metadata* (es. ID documento, file name, path, ecc.).

### 4. Utility e Moduli di Supporto
All’interno della cartella `utils/`, il codice è suddiviso per macro-funzionalità:
- **Processing** (`retriever.py`, `embeddings.py`)  
  - `query_rag_with_gpt` e `query_rag_with_cloud`: eseguono la *similarity search* e poi chiamano la *API* GPT/Claude.  
  - Creazione e gestione embeddings (`create_embeddings`).  
- **Loaders** (`document_loader.py`, `image_manager.py`, `excel_manager.py`)  
  - Forniscono *loader* specializzati per PDF, docx, testi, Excel e persino *image OCR* (con libreria `doctr`).  
- **Formatting** (`formatter.py`)  
  - Formatta le risposte finali, inserendo i riferimenti ai documenti con link e pulsanti di download.  
- **UI Components** (`ui_components.py`)  
  - Gestione del CSS personalizzato.  

---

## Flow di una Richiesta di Domanda (RAG Pipeline)
1. **Inserimento Domanda**: L’utente inserisce un testo libero nella pagina Streamlit (tab “Domande”).  
2. **Verifica del Vector Store**: L’app carica il vector store corrispondente alla KB selezionata.  
3. **Similarity Search**: Viene chiamata la funzione `query_rag_with_gpt` (o `query_rag_with_cloud`), che:
   - Converte la domanda dell’utente in un *embedding vector*.  
   - Cerca i *k* chunk più rilevanti.  
4. **Costruzione Prompt**: I chunk più rilevanti diventano contesto per il modello GPT/Claude.  
5. **Generazione Risposta**: GPT/Claude produce la risposta in linguaggio naturale, arricchita con dettagli contestuali.  
6. **Visualizzazione**: La risposta viene formattata da `formatter.py`, allegando link/nomi dei documenti sorgente.  

---

## Conclusioni
L’architettura del sistema **HelpDeskRAG** si basa su **Streamlit** per la **UI** e si affida a **Chroma** come *vector store* per gestire l’indicizzazione e la ricerca semantica dei contenuti. L’utilizzo del pattern **RAG** consente di fornire risposte di alta qualità, integrate dai dati effettivi conservati nei documenti. Questa struttura modulare rende il sistema estensibile e facilmente manutenibile, favorendo l’aggiunta di nuove tipologie di documenti e nuovi modelli di *large language model* nel futuro.

---

> **Nota**: Il codice mostrato include funzionalità aggiuntive (es. caricamento di siti web con *BeautifulSoup*, login utenti, gestione OCR). Tuttavia, l’impianto principale è organizzato per fornire risposte con un approccio RAG, integrando la potenza dei modelli di linguaggio e un database di documenti semantici (*vector store*).