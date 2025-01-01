# Known Issues and Future Improvements

Questo file elenca i problemi noti e le aree di miglioramento per il progetto. Gli appunti includono suggerimenti e funzionalità da implementare per rendere l'applicazione più robusta ed efficace.

---

## Problemi Noti e Funzionalità Mancanti


### 1. **Implementare il Chunking Semantico (Semantic Chunking) 🧠** 
   - **Descrizione**: Dividere i documenti basandosi sulla coerenza semantica anziché su dimensioni fisse, per preservare il contesto e migliorare la qualità del recupero delle informazioni.
   - **Suggerimento**: Utilizzare librerie NLP come spaCy o NLTK per identificare le sezioni coerenti all'interno dei documenti e modificare le funzioni di caricamento dei documenti per includere il chunking semantico.

---

### 2. **Applicare la Trasformazione delle Query (Query Transformations) 🔄**
   - **Descrizione**: Migliorare l'efficacia del recupero delle informazioni riformulando o ampliando le query degli utenti.
   - **Suggerimento**: Integrare un LLM per generare versioni alternative o più dettagliate delle query prima del processo di recupero.

---

### 3. **Integrare il Re-Ranking Intelligente (Intelligent Reranking) 📈**
   - **Descrizione**: Applicare meccanismi avanzati di scoring per migliorare il ranking di pertinenza dei risultati recuperati.
   - **Suggerimento**: Utilizzare un LLM per valutare la pertinenza dei documenti recuperati e combinare questo punteggio con la similarità vettoriale per ordinare i risultati.

---

### 4. **Utilizzare Contesti Arricchiti (Context Enrichment Techniques) 📝**
   - **Descrizione**: Includere il contesto circostante ai frammenti recuperati per fornire risposte più accurate e contestualizzate.
   - **Suggerimento**: Estendere le funzioni di recupero per includere le frasi precedenti e successive ai frammenti rilevanti.

---

### 5. **Implementare il Self RAG 🔁**
   - **Descrizione**: Adottare un approccio dinamico che decida se utilizzare o meno le informazioni recuperate in base alla query dell'utente.
   - **Suggerimento**: Implementare una logica che valuti la necessità del recupero e che possa generare risposte senza recupero per domande generiche, ottimizzando le risorse.

---

### 6. **Aggiungere l'Estrattore di Segmenti Rilevanti (Relevant Segment Extraction) 🧩**
   - **Descrizione**: Identificare e utilizzare segmenti multi-chunk che forniscono un contesto più completo alle risposte.
   - **Suggerimento**: Analizzare i chunk recuperati per estrarre segmenti più estesi e includerli nel contesto fornito al modello.

---

### 7. **Migliorare l'Explainability con l'Explainable Retrieval 🔍**
   - **Descrizione**: Fornire trasparenza nel processo di recupero per aumentare la fiducia dell'utente e facilitare il miglioramento del sistema.
   - **Suggerimento**: Nella funzione di formattazione delle risposte, aggiungere spiegazioni su come e perché certi documenti o chunk sono stati scelti.

---

### 8. **Implementare Filtri Multi-Faceted 🔍**
   - **Descrizione**: Applicare vari filtri per affinare e migliorare la qualità dei risultati recuperati.
   - **Suggerimento**: Aggiungere metadati ai documenti e permettere agli utenti di filtrare i risultati in base a data, autore, fonte, ecc.

---

### 9. **Ottimizzare l'Interfaccia Utente per una Migliore Esperienza 🌟**
   - **Descrizione**: Migliorare l'usabilità e l'esperienza dell'utente nell'interfaccia dell'applicazione.
   - **Suggerimento**: Aggiungere suggerimenti automatici, esempi di domande e migliorare la visualizzazione delle risposte evidenziando le parti chiave.

---

### 10. **Considerare l'Integrazione di un Knowledge Graph (Graph RAG) 🕸️**
    - **Descrizione**: Integrare dati strutturati da un knowledge graph per arricchire il contesto e migliorare il recupero.
    - **Suggerimento**: Estrarre entità e relazioni dai documenti per costruire un knowledge graph da utilizzare nel processo di recupero.

---

### 11. **Testing RAGAS**
   - **Descrizione**: Integrare un sistema di valutazione con **RAGAS** per testare l'efficacia del motore RAG.
   - **Note**: Questo sarà utile per misurare le prestazioni su diversi knowledge base e modelli di LLM.

---

### 12. **Supporto a Più Database per Knowledge Base**
   - **Descrizione**: Permettere l'uso di più database per gestire knowledge base separate.
   - **Suggerimento**: Implementare una gestione dinamica dei database per consentire all'utente di selezionare o cambiare la knowledge base attiva.

---

### 13. **Gestione di Intere Cartelle (Ricorsiva)**
   - **Descrizione**: Implementare la capacità di caricare intere directory e leggere ricorsivamente tutti i file al loro interno.
   - **Note**: Gestire potenzialmente anche sottocartelle e diversi tipi di file.

---

### 14. **Supporto per Vari Formati di File**
   - **Descrizione**: Supportare vari formati di documenti come PDF, Word, Excel, TXT e JSON.
   - **Suggerimento**: Usare librerie come `PyPDF2`, `python-docx` o `pandas` per elaborare file di diversi tipi.

---

### 15. **Livello di Conoscenza**
   - **Descrizione**: Rendere più efficace il livello di conoscenza selezionabile (beginner, intermediate, expert).
   - **Note**: Personalizzare la granularità delle risposte generate dagli LLM in base al livello di competenza selezionato, magari adattando il prompt o utilizzando modelli diversi.

---

### 16. **Riferimenti Linkabili**
   - **Descrizione**: Creare riferimenti cliccabili che indirizzano direttamente al documento o alla sezione relativa.
   - **Note**: Aggiungere una funzionalità per mostrare i link nel formato markdown o HTML, facilitando l'accesso alle fonti originali.

---

### 17. **Riferimento agli LLM nella Cronologia**
   - **Descrizione**: Associare ogni interazione nella cronologia a un riferimento chiaro al modello LLM utilizzato (ad esempio, GPT o Claude).
   - **Note**: Mostrare l'informazione nella sidebar accanto alla domanda/risposta.

---

## Codice da Rivedere

### 1. **Ottimizzazione della Divisione dei Documenti in Chunk**
   - **Blocco rilevante**: 
     ```python
     # Divide i documenti in chunk più piccoli.
     text_splitter = RecursiveCharacterTextSplitter(
         chunk_size
     )
     ```
   - **Problema**: Necessario ottimizzare la dimensione dei chunk per evitare perdita di contesto o dati ridondanti.
   - **Suggerimento**: Implementare il chunking semantico per dividere i documenti in base alla coerenza semantica anziché su dimensioni fisse.

---

### 2. **Migliorare la Ricerca Semantica e il Filtraggio dei Risultati**
   - **Blocco rilevante**: 
     ```python
     results = db.max_marginal_relevance_search()
     results = db.similarity_search_with_relevance_scores(query_text, k=3)
     ```
   - **Problema**: Assicurarsi che la ricerca semantica restituisca risultati rilevanti e diversificati, evitando duplicati.
   - **Suggerimento**: Integrare il re-ranking intelligente e filtri multi-faceted per migliorare la pertinenza e la diversità dei risultati.

---

### 3. **Estendere il Contesto nelle Risposte**
   - **Blocco rilevante**: Processi di formattazione e generazione delle risposte.
   - **Suggerimento**: Utilizzare contesti arricchiti includendo le frasi precedenti e successive ai frammenti recuperati, per fornire risposte più complete e accurate.

---

### 4. **Implementare l'Explainable Retrieval nel Codice**
   - **Blocco rilevante**: Funzione `format_response` o simili.
   - **Suggerimento**: Modificare il codice per aggiungere spiegazioni su come e perché certi documenti o chunk sono stati scelti, migliorando la trasparenza per l'utente.

---

## Strumenti da Esplorare

- **Giskard**: Valutare se questo strumento può essere utile per testing e debugging del progetto.
- **RAGAS**: Strumento per la valutazione delle prestazioni di sistemi RAG.

---


---