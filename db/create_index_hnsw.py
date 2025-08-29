# index_runner.py
from pgvector.psycopg2 import register_vector
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path


def main():
    load_dotenv()
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    RAM_LIMIT = os.getenv("RAM_LIMIT", "14GB")
    MIN_ROW_COUNT = 20000
    # connect to the database
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )
    connection.autocommit = True
    register_vector(connection)

    cursor = connection.cursor()

    cursor.execute("SET maintenance_work_mem = %s;", (RAM_LIMIT,))
    cursor.execute(
        """
        SELECT source_id, COUNT(*) AS cnt
        FROM related_text
        GROUP BY source_id
        """
    )
    for source_id, count in cursor.fetchall():
        if count < MIN_ROW_COUNT:
            print(
                f"Skipping source_id {source_id} with count {count} < {MIN_ROW_COUNT}"
            )
            continue
        print("Creating index for source_id:", source_id)
        idx_name = f"related_text_embed_hnsw_cos_src_{source_id}"
        sql = f"""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name}
        ON Related_text USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 128)
        WHERE source_id = %s;
        """
        cursor.execute(sql, (source_id,))

    with open("db/index.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    for query in [s.strip() for s in sql.split(";") if s.strip()]:
        print("Running query:\n", query)
        cursor.execute(query + ";")
        print("-----------------------------------------------")
    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()
