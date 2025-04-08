import sqlite3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine


def migrate_sqlite_to_postgres():
    """Hauptsteuerungs-Logik der App."""

    # *** Schritt 1: Passwort für Benutzer "app_user" setzen ***
    # PostgreSQL-Verbindung als Admin (Benutzer "postgres")
    admin_pg_url = "postgresql://postgres@141.244.158.202:5432/postgres"
    admin_pg_engine = create_engine(admin_pg_url)

    with admin_pg_engine.connect() as conn:
        # Passwort für app_user setzen (falls noch nicht vorhanden)
        conn.execute("ALTER USER app_user WITH PASSWORD 'password123';")
        print("✅ Passwort für Benutzer 'app_user' wurde gesetzt.")

    # *** Schritt 2: PostgreSQL-Verbindung mit Benutzer und Passwort verwenden ***
    pg_url = "postgresql://app_user:password123@141.244.158.202:5432/samples"
    pg_engine = create_engine(pg_url)

    # *** Schritt 3: Migration der SQLite-Datenbank ***
    # SQLite-Datenbankpfad
    sqlite_path = "/Volumes/INFO/Analyseergebnisse/samples.db"
    sqlite_conn = sqlite3.connect(sqlite_path)

    # Tabellen, die du übertragen willst
    tables = ["samples", "users", "chn_data", "eltra_tga_data"]

    # Übertragen der Tabellen
    for table in tables:
        print(f"🚀 Migrating '{table}'...")
        df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
        df.to_sql(table, con=pg_engine, if_exists="replace", index=False)
        print(f"✅ Table '{table}' migrated successfully.")

    # SQLite-Verbindung schließen
    sqlite_conn.close()
    print("🎉 Migration abgeschlossen.")


if __name__ == "__main__":
    migrate_sqlite_to_postgres()
