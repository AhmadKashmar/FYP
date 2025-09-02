import os
import requests
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
import sentence_transformers
import torch
import numpy as np
import warnings
import traceback
from random import randint
from datetime import datetime
from playground.utils import TextCleaner

cleaner = TextCleaner()
load_dotenv()
model_name = os.environ.get("EMBEDDING_MODEL")

BATCH_SIZE = 2000


class Transformer:
    transformer = None

    @staticmethod
    def load(model_name: str = model_name):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model {model_name} on {device}...")
        warnings.filterwarnings("ignore")
        Transformer.transformer = sentence_transformers.SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=True,
        )
        warnings.filterwarnings("default")

    @staticmethod
    def embeddings(text: str) -> np.ndarray:
        text = cleaner.cleanText(text)
        return Transformer.transformer.encode(
            text,
            # task="retrieval.passage",
            normalize_embeddings=True,
        )


class JinaAPIEmbedder:
    api_url = "https://api.jina.ai/v1/embeddings"
    idx = 0
    JINA_API_KEYS = os.getenv("JINA_API_KEY").split(",")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEYS[idx]}",
    }

    @staticmethod
    def embeddings(texts: list[str]) -> list[list[float]]:
        texts = [cleaner.cleanText(text) for text in texts]
        try:
            payload = {
                "model": "jina-embeddings-v3",
                "task": "retrieval.passage",
                "input": texts,
            }
            resp = requests.post(
                JinaAPIEmbedder.api_url,
                headers=JinaAPIEmbedder.headers,
                json=payload,
            )
            resp.raise_for_status()
            body = resp.json()
        except Exception as e:
            print(
                f"API key {JinaAPIEmbedder.JINA_API_KEYS[JinaAPIEmbedder.idx]} is exhausted, switching..."
            )
            JinaAPIEmbedder.idx += 1
            if JinaAPIEmbedder.idx == len(JinaAPIEmbedder.JINA_API_KEYS):
                print(e)
                raise RuntimeError("All API keys exhausted")
            JinaAPIEmbedder.headers["Authorization"] = (
                f"Bearer {JinaAPIEmbedder.JINA_API_KEYS[JinaAPIEmbedder.idx]}"
            )
            return JinaAPIEmbedder.embeddings(texts)
        return [item["embedding"] for item in body["data"]]


def fetch_pending(
    cursor: psycopg2.extensions.cursor,
    table: str,
    pk_cols: list[str],
    text_col: str,
    limit: int,
):
    pk_list = ", ".join(pk_cols)
    query = f"""
        SELECT {pk_list}, {text_col}
          FROM {table}
         WHERE embedding IS NULL
         LIMIT {limit}
    """
    cursor.execute(query)
    return cursor.fetchall()


def update_batch(
    cursor,
    table: str,
    pk_cols: list[str],
    embeddings: list[list[float]],
    pk_values: list[tuple],
):
    set_clause = "embedding = %s"
    where_clause = " AND ".join(f"{col} = %s" for col in pk_cols)
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    params = [[vec] + list(pk) for vec, pk in zip(embeddings, pk_values)]
    psycopg2.extras.execute_batch(cursor, query, params, page_size=50)


def process_table(
    connection: psycopg2.extensions.connection,
    table: str,
    pk_cols: list[str],
    text_col: str,
):
    with connection.cursor() as cur:
        while True:
            batch = fetch_pending(cur, table, pk_cols, text_col, BATCH_SIZE)
            if not batch:
                break

            pk_values = [tuple(row[: len(pk_cols)]) for row in batch]
            texts = [row[-1] for row in batch]
            try:
                embeddings = Transformer.embeddings(texts)
            except RuntimeError as e:
                print(f"Error fetching embeddings: {e}")
                break
            update_batch(cur, table, pk_cols, embeddings, pk_values)
            connection.commit()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{now}] Updated {len(batch)} rows in `{table}`" + "." * randint(1, 20)
            )


def show_progress(conn: psycopg2.extensions.connection):
    with conn.cursor() as cur:
        print("Number of embedded rows: ")
        print("Related_text: ", end="")
        query = """
            SELECT COUNT(*)
              FROM Related_text
             WHERE embedding IS NOT NULL
        """
        cur.execute(query)
        count = cur.fetchone()[0]
        print(count)
        print("Number of rows to be embedded: ")
        print("Related_text: ", end="")
        query = """
            SELECT COUNT(*)
              FROM Related_text
             WHERE embedding IS NULL
        """
        cur.execute(query)
        count = cur.fetchone()[0]
        print(count)


def main():

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    register_vector(conn)
    # show_progress(conn)
    Transformer.load(model_name)

    try:
        process_table(conn, "Sentence", ["sentence_id", "section_id"], "text")
        process_table(conn, "Related_text", ["related_id"], "details")
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        show_progress(conn)
        conn.close()


if __name__ == "__main__":
    main()
