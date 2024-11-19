
# Retrieval-Augmented Generation (RAG) System

Questo progetto implementa un sistema RAG, che utilizza un modello di linguaggio avanzato (ad esempio OpenAI GPT) per rispondere a domande complesse utilizzando una knowledge base esterna, basata su ChromaDB. L’obiettivo principale del sistema è fornire risposte contestuali e accurate per il dominio di applicazione prescelto, con la possibilità di gestire documenti di riferimento e mantenere una cronologia delle interazioni.

## Funzionalità principali

### 1. Domanda e Risposta (Q&A)
L'utente può inserire una domanda nell'interfaccia principale, e il sistema:
   - Recupera informazioni rilevanti dalla knowledge base tramite una ricerca di similarità.
   - Genera una risposta utilizzando il modello di linguaggio, fornendo riferimenti a documenti pertinenti quando applicabile.
   - Se non ci sono informazioni rilevanti o se la domanda è fuori contesto, il sistema risponde con un messaggio di cortesia.

### 2. Contesto Aggiuntivo e Continuità
   - Il sistema memorizza la risposta immediatamente precedente per arricchire le domande successive, migliorando la continuità e la coerenza delle risposte.
   - Ogni domanda viene potenzialmente migliorata con il contesto precedente per evitare risposte fuori contesto.

### 3. Knowledge Base con ChromaDB
   - Utilizza ChromaDB come database di vettori per memorizzare e recuperare informazioni di riferimento.
   - La knowledge base può essere aggiornata, consentendo l'inserimento di nuovi documenti, rendendo il sistema facilmente adattabile.

### 4. Cronologia delle Interazioni
   - Mantiene una cronologia delle domande e delle risposte passate, visibile nella barra laterale.
   - La cronologia è ordinata in modo da mostrare le interazioni più recenti in alto, consentendo una navigazione facile e veloce delle domande precedenti.

### 5. Gestione Documenti
   - Sezione dedicata alla gestione dei documenti, dove è possibile caricare, rimuovere o aggiornare i contenuti della knowledge base.
   - Questa funzione consente agli utenti di adattare facilmente la base di conoscenza aggiungendo nuovi documenti o sostituendo quelli obsoleti.

## Struttura del Codice

- **`main.py`**: il file principale dell’applicazione. Contiene l'interfaccia utente con Streamlit e gestisce le interazioni dell'utente.
- **`utils/retriever.py`**: implementa la logica di recupero delle informazioni da ChromaDB e il prompt per la risposta del modello.
- **`database.py`**: gestisce la creazione e il caricamento del database ChromaDB.
- **`config.py`**: carica le configurazioni, incluse le chiavi API.
- **`ui_components.py`**: contiene le impostazioni di stile per personalizzare l’interfaccia utente.

## Configurazione

1. **Impostazioni API**: assicurarsi di inserire la chiave API di OpenAI nel file `.env` o direttamente nella configurazione.
2. **Path per ChromaDB**: il database si trova di default nel percorso `CHROMA_PATH = "chroma"`, ma è possibile personalizzare questo percorso nel file `database.py`.

## Esecuzione

1. Clonare il repository.
2. Installare le dipendenze con:
   ```bash
   pip install -r requirements.txt
   ```
3. Eseguire l’app con:
   ```bash
   streamlit run app.py
   ```

---

## Esempio di Utilizzo

1. **Domanda**: Inserisci una domanda nella casella di testo e ottieni una risposta con riferimenti pertinenti dalla knowledge base.
2. **Gestione Documenti**: Vai alla sezione *Gestione Documenti* per caricare nuovi file o aggiornare la base di conoscenza.
3. **Cronologia**: Consulta la cronologia delle domande passate per navigare facilmente tra le risposte.

---

## Requisiti

- **Python 3.7+**
- **Streamlit** per l’interfaccia utente
- **OpenAI API** per il modello di linguaggio
- **ChromaDB** per il database di vettori

## Note aggiuntive

Questo sistema è progettato per supportare interazioni iterative e basate sul contesto. La funzionalità di memoria delle risposte precedenti arricchisce il dialogo, mentre la cronologia facilita l’accesso a risposte passate per migliorare l’esperienza complessiva dell’utente.

--- 


Questa guida offre una panoramica completa del progetto, spiegando come utilizzare ciascuna funzionalità principale e configurare il sistema.