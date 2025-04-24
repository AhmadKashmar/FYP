# Setup

1. Install Docker & Docker Compose (if you haven’t already).

2. Create a `.env` file in the project root and fill in your values.

```.env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=your_db_port
```

3. Create a `docker-compose.yml` at the root (or use the one provided).

4. Start Postgres:

    ```bash
    docker-compose up -d postgres
    ```

5. Load your CSV data into the database (you might want to edit the column names in db/csv_to_db.py to fit your data, or create a new script to migrate it):

    ```bash
    python db/csv_to_db.py
    ```

6. Change the VECTOR_DIM value in `db/alter_tables.py` to match your embedding model (currently set to 1024), then create that column.

    ```bash
     python db/alter_tables.py
    ```

7. Compute and store embeddings (can be stopped with Ctrl+C, picks up where it left off):

    ```bash
    python db/update_tables.py
    ```

At this point your data (and embeddings) are in the Postgres container.

Notes:

-   when you stop and start docker, make sure postgres is running (step 4).
