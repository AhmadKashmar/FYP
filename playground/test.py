import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
import sentence_transformers
import torch
import numpy as np
import time
import warnings


last_print_time = None


def timed_print(msg: str):
    """
    Prints the given message along with the elapsed time (in ms) since the last timed_print.
    On the very first call, it treats the elapsed time as 0.00 ms.
    """
    global last_print_time
    now = time.time()

    if last_print_time is None:

        elapsed_ms = 0.0
    else:
        elapsed_ms = (now - last_print_time) * 1000

    print(f"{msg} (Elapsed since last print: {elapsed_ms:.2f} ms)")

    last_print_time = now


class Transformer:
    transformer = None

    @staticmethod
    def load(model_name: str = "jinaai/jina-embeddings-v3"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        timed_print(f"Loading model {model_name} on {device}...")
        warnings.filterwarnings("ignore")
        Transformer.transformer = sentence_transformers.SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=True,
        )
        warnings.filterwarnings("default")
        timed_print("Model loaded successfully.")

    @staticmethod
    def embeddings(text: str) -> np.ndarray:
        return Transformer.transformer.encode(text, task="retrieval.query")


def find_related_sentences(query: str) -> list[str]:
    if Transformer.transformer is None:
        Transformer.load()

    timed_print("Generating embeddings for the query...")
    query_embedding = Transformer.embeddings(query)
    timed_print("Query embedding generated successfully.")

    load_dotenv()
    conn = None
    results = []

    try:
        timed_print("Connecting to the database...")
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        register_vector(conn)
        timed_print("Connected to the database successfully.")

        with conn.cursor() as cur:
            sql_query = """
                WITH filtered_related AS (
                    SELECT
                        related_id,
                        1 - (embedding <=> %(query_embedding)s) AS similarity
                    FROM
                        Related_text
                    WHERE
                        1 - (embedding <=> %(query_embedding)s) > %(similarity_threshold)s
                    ORDER BY
                        embedding <=> %(query_embedding)s
                    LIMIT %(k)s
                )
                SELECT DISTINCT
                    s.text
                FROM
                    Sentence AS s
                    JOIN relationship AS r
                        ON s.sentence_id = r.sentence_id
                    AND s.section_id  = r.section_id
                    JOIN filtered_related AS fr
                        ON r.related_text_id = fr.related_id;
            """
            params = {
                "query_embedding": query_embedding,
                "k": 30,
                "similarity_threshold": 0.5,
            }
            timed_print("Executing SQL query...")
            cur.execute(sql_query, params)
            timed_print("SQL query executed successfully.")
            rows = cur.fetchall()
            results = [row[0] for row in rows]

    except (Exception, psycopg2.Error) as error:
        timed_print(f"An error occurred: {error}")
        return []
    finally:
        if conn is not None:
            conn.close()
            timed_print("Database connection closed.")

    return results


if __name__ == "__main__":

    last_print_time = None

    sample_query = "الاخلاق"
    timed_print(f"Searching for sentences related to: '{sample_query}'")
    related_sentences = find_related_sentences(sample_query)

    if related_sentences:
        timed_print(f"Found {len(related_sentences)} related sentences:")
        for i, sentence in enumerate(related_sentences, 1):
            print(f"{i}. {sentence}")
        timed_print("Finished printing all sentences.")
    else:
        timed_print("No related sentences found matching the criteria.")
