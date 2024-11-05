# utils/formatter.py

def format_response(answer, references):
    """
    Formatta la risposta in Markdown e aggiunge i documenti di riferimento solo se presenti.

    Parameters:
    - answer (str): Il testo della risposta generata dall'IA.
    - references (list of str): Un elenco dei nomi dei documenti di riferimento.

    Returns:
    - str: La risposta formattata in Markdown.
    """
    # Normalizza e formatta il testo della risposta
    formatted_answer = f"### 📝 Risposta\n\n{answer}\n\n---"

    # Aggiungi la sezione dei riferimenti solo se ci sono documenti nella lista
    if references:
        unique_references = "\n".join([f"- {ref}" for ref in set(references)])
        references_section = f"\n\n### 📄 Documenti di Riferimento\n{unique_references}\n\n---"
    else:
        references_section = ""

    # Aggiungi una nota finale, se necessario
    #note_section = "\n\n_Nota: Le informazioni sono state generate utilizzando i documenti pertinenti._" if references else ""

    # Struttura Markdown finale della risposta
    full_formatted_answer = f"{formatted_answer}{references_section}"

    return full_formatted_answer
