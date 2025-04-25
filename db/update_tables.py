import os
import requests
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()
JINA_API_KEYS = os.getenv("JINA_API_KEY").split(",")
BATCH_SIZE = 128

class Transformer:
    api_url = "https://api.jina.ai/v1/embeddings"
    model_name: str
    idx = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEYS[idx]}",
    }

    @staticmethod
    def load(model_name: str):
        Transformer.model_name = model_name
        print(f"Configured to fetch embeddings from Jina API model '{model_name}'")

    @staticmethod
    def embeddings(texts: list[str]) -> list[list[float]]:
        try:
            if not hasattr(Transformer, "model_name"):
                raise RuntimeError("Model not set; call Transformer.load() first")
            payload = {
                "model": Transformer.model_name,
                "task": "retrieval.passage",
                "input": texts,
            }
            resp = requests.post(
                Transformer.api_url,
                headers=Transformer.headers,
                json=payload,
            )
            resp.raise_for_status()
            body = resp.json()
        except:
            print(
                f"API key {JINA_API_KEYS[Transformer.idx]} is exhausted, switching..."
            )
            Transformer.idx += 1
            if Transformer.idx == len(JINA_API_KEYS):
                raise RuntimeError("All API keys exhausted")
            Transformer.headers["Authorization"] = (
                f"Bearer {JINA_API_KEYS[Transformer.idx]}"
            )
            return Transformer.embeddings(texts)
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
         ORDER BY {pk_list}
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
            print(f"Updated {len(batch)} rows in `{table}`")


def main():
    Transformer.load("jina-embeddings-v3")

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    register_vector(conn)

    try:
        process_table(conn, "Sentence", ["sentence_id", "section_id"], "text")
        process_table(conn, "Related_text", ["related_id"], "details")
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
