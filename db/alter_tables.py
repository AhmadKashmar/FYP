import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv


def main():
    load_dotenv()
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    register_vector(conn)

    VECTOR_DIM = 768  # placeholder for now

    queries = [
        f"ALTER TABLE Sentence ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM});",
        f"ALTER TABLE Related_text ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM});",
    ]

    with conn.cursor() as cur:
        for query in queries:
            cur.execute(query)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
