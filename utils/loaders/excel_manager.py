import pandas as pd
import streamlit as st

class ExcelManager:
    """
    Classe per gestire file Excel:
    - Caricamento dei dati da file Excel
    - Visualizzazione dei dati
    - Estrazione del contenuto per altre elaborazioni
    """

    def __init__(self):
        pass

    def load_excel(self, file):
        """
        Carica un file Excel in un DataFrame.
        :param file: File caricato (streamlit file uploader)
        :return: DataFrame
        """
        try:
            # Legge il file Excel in un DataFrame
            df = pd.read_excel(file)
            return df
        except Exception as e:
            st.error(f"Errore durante il caricamento del file Excel: {e}")
            return None

    def preview_excel(self, df, max_rows=10):
        """
        Mostra un'anteprima del DataFrame.
        :param df: DataFrame da visualizzare
        :param max_rows: Numero massimo di righe da visualizzare
        """
        if df is not None:
            st.write("**Anteprima del File Excel:**")
            st.dataframe(df.head(max_rows))
        else:
            st.error("DataFrame non valido o vuoto.")

    def extract_text_from_excel(self, df):
        """
        Converte il contenuto del DataFrame in stringa per l'elaborazione.
        :param df: DataFrame da convertire
        :return: Stringa rappresentante i dati
        """
        if df is not None:
            return df.to_string(index=False)
        else:
            st.error("DataFrame non valido o vuoto.")
            return ""

    def process_excel(self, file):
        """
        Processa un file Excel e ritorna i dati come stringa.
        :param file: File caricato (streamlit file uploader)
        :return: Stringa rappresentante i dati
        """
        st.write(f"📊 Elaborando il file Excel: {file.name}")
        df = self.load_excel(file)
        self.preview_excel(df)
        extracted_text = self.extract_text_from_excel(df)
        return extracted_text
