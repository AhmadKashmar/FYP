import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
import numpy as np
import sentence_transformers
import torch
import warnings


class Transformer:

    transformer = None

    @staticmethod
    def load(model_name: str):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model {model_name} on {device}...")
        warnings.filterwarnings("ignore")
        Transformer.transformer = sentence_transformers.SentenceTransformer(
            model_name,
            device=device,
        )
        warnings.filterwarnings("default")
        Transformer.cached_embeddings = {}

    @staticmethod
    def embeddings(text: str) -> np.ndarray:
        return Transformer.transformer.encode(text, convert_to_numpy=True)


BATCH_SIZE = 128


def fetch_pending(cursor, table, pk_cols, text_col, limit):
    pk_list = ", ".join(pk_cols)
    query = (
        f"SELECT {pk_list}, {text_col} "
        f"FROM {table} "
        f"WHERE embedding IS NULL "
        f"ORDER BY {pk_list} "
        f"LIMIT {limit}"
    )
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows


def update_batch(
    cursor: psycopg2.extensions.cursor,
    table: str,
    pk_cols: list[str],
    embeddings: np.ndarray,
    pk_values: list[tuple],
):
    set = "embedding = %s"
    where_clause = " AND ".join(f"{col} = %s" for col in pk_cols)
    query = f"UPDATE {table} SET {set} WHERE {where_clause}"
    params = []
    for vec, pk in zip(embeddings, pk_values):
        params.append([vec] + list(pk))
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
            embeddings = [Transformer.embeddings(text) for text in texts]
            update_batch(cur, table, pk_cols, embeddings.tolist(), pk_values)
            connection.commit()
            print(f"Updated {len(batch)} rows in `{table}`")


def main():
    model = "Omartificial-Intelligence-Space/Arabic-Triplet-Matryoshka-V2"
    Transformer.load(model)

    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    register_vector(connection)

    try:
        process_table(
            connection,
            table="Sentence",
            pk_cols=["sentence_id", "section_id"],
            text_col="text",
        )
        process_table(
            connection,
            table="Related_text",
            pk_cols=["related_id"],
            text_col="details",
        )

    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
