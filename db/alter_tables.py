import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv


def main():
    if (
        input(
            "This will delete the embeddings from the database. Are you sure? (y/n): "
        ).lower()
        != "y"
    ):
        print("Not Confirmed...")
        return
    load_dotenv()
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    register_vector(conn)

    VECTOR_DIM = 1024

    queries = [
        "ALTER TABLE Sentence DROP COLUMN IF EXISTS embedding;",
        f"ALTER TABLE Sentence ADD COLUMN embedding vector({VECTOR_DIM});",
        "ALTER TABLE Related_text DROP COLUMN IF EXISTS embedding;",
        f"ALTER TABLE Related_text ADD COLUMN embedding vector({VECTOR_DIM});",
    ]
    with conn.cursor() as cur:
        for query in queries:
            cur.execute(query)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
