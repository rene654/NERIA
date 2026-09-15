import os
import psycopg
def main() -> None:
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD no está disponible en el entorno."
        )
    connection_settings = {
        "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "dbname": os.environ.get("POSTGRES_DB", "neria"),
        "user": os.environ.get("POSTGRES_USER", "neria_dev"),
        "password": password,
        "connect_timeout": 5,
    }
    with psycopg.connect(**connection_settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user;"
            )
            database_name, database_user = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) FROM meta.schema_migrations;"
            )
            migration_count = cursor.fetchone()[0]
    print(f"Database: {database_name}")
    print(f"User: {database_user}")
    print(f"Applied migrations: {migration_count}")
    print("Connection test: PASS")
if __name__ == "__main__":
    main()