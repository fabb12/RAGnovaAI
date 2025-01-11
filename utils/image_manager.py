from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector


class ImageManager:
    """
    Classe per gestire immagini:
    - Estrazione testo (OCR)
    - Generazione embedding
    - Salvataggio embedding nel database
    """
    def __init__(self, db_connection_string, embedding_model_name="thenlper/gte-base"):
        # Modello OCR
        self.ocr_model = ocr_predictor(pretrained=True)
        # Modello di embedding
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"batch_size": 4}
        )
        # Connessione al database
        self.db_connection_string = db_connection_string

    def extract_text(self, image_path):
        """
        Estrae testo da un'immagine.
        :param image_path: Percorso all'immagine
        :return: Testo estratto
        """
        img = DocumentFile.from_images(image_path)
        ocr_result = self.ocr_model(img)
        return ocr_result.render()

    def generate_embedding(self, text):
        """
        Genera embedding dal testo estratto.
        :param text: Testo estratto
        :return: Vettore di embedding
        """
        return self.embedding_model.embed_documents([text])[0]

    def save_to_database(self, text, embedding, source):
        """
        Salva testo, embedding e percorso sorgente nel database.
        :param text: Testo estratto
        :param embedding: Vettore di embedding
        :param source: Percorso al file sorgente
        """
        with psycopg.connect(self.db_connection_string) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO infographic (text, source, embedding) VALUES (%s, %s, %s)",
                    (text, source, embedding)
                )

    def process_image(self, image_path):
        """
        Processa un'immagine: OCR, embedding, salvataggio nel database.
        :param image_path: Percorso all'immagine
        :return: Dizionario con informazioni elaborate
        """
        text = self.extract_text(image_path)
        embedding = self.generate_embedding(text)
        self.save_to_database(text, embedding, image_path)
        return {"text": text, "embedding": embedding, "source": image_path}

    def process_directory(self, directory_path, file_extensions=[".jpg", ".png"]):
        """
        Processa tutte le immagini in una directory (ricorsivo).
        :param directory_path: Percorso alla directory
        :param file_extensions: Tipi di file da processare
        :return: Lista di risultati elaborati
        """
        directory = Path(directory_path)
        results = []
        for file_path in directory.rglob("*"):
            if file_path.suffix.lower() in file_extensions:
                try:
                    results.append(self.process_image(file_path))
                except Exception as e:
                    print(f"Errore durante l'elaborazione di {file_path}: {e}")
        return results
