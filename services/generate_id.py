import sqlite3
import datetime

from services.database import get_db_path


def generate_sample_id(prefix: str) -> str:
    """
    Generiert eine einzigartige Sample-ID im Format PREFIX_JAHR_XXXX,
    wobei nur das Jahr berücksichtigt wird.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Tabelle erstellen, falls sie noch nicht existiert
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            sample_id TEXT PRIMARY KEY  -- Nur die vollständige Sample-ID wird gespeichert
        )
    """)

    try:
        # Hole das aktuelle Jahr (z. B. "23" für 2023)
        year = datetime.datetime.now().strftime("%y")

        # Prüfe die höchste laufende Nummer (XXXX) für das aktuelle Jahr (unabhängig vom Prefix)
        cursor.execute("""
            SELECT MAX(CAST(SUBSTR(sample_id, -4) AS INTEGER))
            FROM samples
            WHERE sample_id LIKE ?
        """, (f"%_{year}_%",))
        result = cursor.fetchone()[0]

        # Wenn keine bestehende Nummer gefunden wurde, starte mit 1
        next_counter = (result + 1) if result else 1

        # Erstelle die ID im gewünschten Format (PREFIX_JAHR_XXXX)
        sample_id = f"{prefix}_{year}_{next_counter:04d}"


        return sample_id  # Gib die generierte ID zurück

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Fehler bei der SQL-Operation: {e}")
        raise RuntimeError(f"Fehler bei der ID-Generierung: {repr(e)}")

    finally:
        conn.close()
