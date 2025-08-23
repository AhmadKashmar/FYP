# Setup

1. Install Docker & Docker Compose (if you haven’t already).

2. Create a `.env` file in the project root and fill in your values. Make sure HOST_DATA_PATH is set in a similar format.

    ```.env
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_PORT=your_db_port
    HOST_DATA_PATH=//c/Users/ahmad/Desktop:
    DATA_DIR=directory/containing/csv/files
    VECTOR_DIM ="1024" # dimensions of the embedding vectors
    RAM_LIMIT="14GB" # how much ram usable while indexing database (default 64MB limit makes it impossible)
    ```

3. Create a postgres container with the following command:

    ```bash
    docker run --name basic-postgres -e POSTGRES_USER="$env:DB_USER" -e POSTGRES_PASSWORD="$env:DB_PASSWORD" -e POSTGRES_DB="$env:DB_NAME"  -e PGDATA="/var/lib/postgresql/data/pgdata" -v "$($env:HOST_DATA_PATH)/data/pgdata:/var/lib/postgresql/data" -p "$($env:DB_PORT):5432" -d -it ankane/pgvector:latest
    ```

4. Load your CSV data into the database (you might want to edit the column names in `db/csv_to_db.py` to fit your data, or create a new script to migrate it):

    ```bash
    python db/csv_to_db.py
    ```

5. Create embeddings column.

    ```bash
     python db/alter_tables.py
    ```

6. Compute and store embeddings (can be stopped with Ctrl+C, picks up where it left off):

    ```bash
    python db/update_tables.py
    ```

7. Index the database by running the following (it will take a few minutes):
    ```bash
    python db/create_index_hnsw.py
    ```

At this point your data (and embeddings) are in the Postgres container.

Notes:

-   when you stop and start docker, make sure postgres is running.

# Web App Setup

1. Go to the directory `web-app` and install node requirements, then build

    ```bash
    npm install; npm run build;
    ```

2. Start the server, and load the web app
    ```bash
    python -m server.app; cd web-app/; npx serve -s build;
    ```
