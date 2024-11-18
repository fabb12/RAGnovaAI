# Known Issues and Future Improvements

Questo file elenca i problemi noti e le aree di miglioramento per il progetto. Gli appunti includono suggerimenti e funzionalità da implementare per rendere l'applicazione più robusta ed efficace.

---

## Problemi Noti e Funzionalità Mancanti

### **Integrare funzionalita del progetto RAG GPT**
--------------------



### 1. **Testing RAGAS**
   - **Descrizione**: Integrare un sistema di valutazione con **RAGAS** per testare l'efficacia del motore RAG.
   - **Note**: Questo sarà utile per misurare le prestazioni su diversi knowledge base e modelli di LLM.

---

### 2. **Supporto a Più Database per Knowledge Base**
   - **Descrizione**: Permettere l'uso di più database per gestire knowledge base separate.
   - **Suggerimento**: Implementare una gestione dinamica dei database per consentire all'utente di selezionare o cambiare la knowledge base attiva.

---

### 3. **Gestione di Intere Cartelle (Ricorsiva)**
   - **Descrizione**: Implementare la capacità di caricare intere directory e leggere ricorsivamente tutti i file al loro interno.
   - **Note**: Gestire potenzialmente anche sottocartelle e diversi tipi di file.

---

### 4. **Supporto per Vari Formati di File**
   - **Descrizione**: Supportare vari formati di documenti come PDF, Word, Excel, TXT, e JSON.
   - **Suggerimento**: Usare librerie come `PyPDF2`, `python-docx`, o `pandas` per elaborare file di diversi tipi.

---

### 5. **Livello di Conoscenza**
   - **Descrizione**: Rendere più efficace il livello di conoscenza selezionabile (beginner, intermediate, expert).
   - **Note**: Personalizzare la granularità delle risposte generate dagli LLM in base al livello di competenza selezionato.

---

### 6. **Riferimenti Linkabili**
   - **Descrizione**: Creare riferimenti cliccabili che indirizzano direttamente al documento o alla sezione relativa.
   - **Note**: Aggiungere una funzionalità per mostrare i link nel formato markdown o HTML.

---

### 7. **Riferimento agli LLM nella Cronologia**
   - **Descrizione**: Associare ogni interazione nella cronologia a un riferimento chiaro al modello LLM utilizzato (ad esempio, GPT o Claude).
   - **Note**: Mostrare l'informazione nella sidebar accanto alla domanda/risposta.

---

## Codice da Rivedere

### 1. **Divisione dei Documenti in Chunk**
   - **Blocco rilevante**: 
     ```python
     # Divide i documenti in chunk più piccoli.
     text_splitter = RecursiveCharacterTextSplitter(
         chunk_size
     )
     ```
   - **Problema**: Necessario ottimizzare la dimensione dei chunk per evitare perdita di contesto o dati ridondanti.

---

### 2. **Ricerca Semantica e Filtraggio dei Risultati**
   - **Blocco rilevante**: 
     ```python
     results = db.max_marginal_relevance_search()
     results = db.similarity_search_with_relevance_scores(query_text, k=3)
     ```
   - **Problema**: Assicurarsi che la ricerca semantica restituisca risultati rilevanti e diversificati, evitando duplicati.

---

## Strumenti da Esplorare
- **Giskard**: Valutare se questo strumento può essere utile per testing e debugging del progetto.

---

## Note Finali
Continuare a iterare e migliorare il progetto basandosi sui feedback degli utenti e sui test di integrazione con diverse knowledge base.
