import sqlite3
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

from services.database import get_db_path


def manage_postgres():
    """Nur Admins dürfen Datenbankoperationen durchführen."""
    if st.session_state.get("role") != "admin":
        st.warning("Keine Berechtigung! Nur Admins dürfen diese Aktion ausführen.")
        return

    st.write("Willkommen im PostgreSQL-Verwaltungsbereich!")

    # Migration durchführen
    if st.button("Migration starten"):
        # PostgreSQL-Verbindung
        pg_url = "postgresql://app_user:your_password@141.244.158.202:5432/samples"
        pg_engine = create_engine(pg_url)

        # SQLite-Verbindung
        sqlite_path = get_db_path()
        sqlite_conn = sqlite3.connect(sqlite_path)

        # Tabellen, die migriert werden sollen
        tables = ["samples", "users", "chn_data", "eltra_tga_data"]

        try:
            for table in tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
                df.to_sql(table, con=pg_engine, if_exists="replace", index=False)
                st.success(f"✅ Tabelle '{table}' erfolgreich migriert!")

        except Exception as e:
            st.error(f"Fehler bei der Migration: {e}")

        finally:
            sqlite_conn.close()
            pg_engine.dispose()
