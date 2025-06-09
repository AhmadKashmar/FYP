from pgvector.psycopg2 import register_vector
import psycopg2
from dotenv import load_dotenv
import os


def main():
    load_dotenv()
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    # connect to the database
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )
    register_vector(connection)
    cursor = connection.cursor()

    with open("db/index.sql", "r") as f:
        sql = f.read()
    cursor.execute(sql)
    connection.commit()


if __name__ == "__main__":
    main()
