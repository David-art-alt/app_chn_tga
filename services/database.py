import base64
import os
import sqlite3
from sqlite3 import OperationalError

import bcrypt
import logging
import pandas as pd
import sqlalchemy
import streamlit as st
from sqlalchemy import create_engine, text


# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

#DB_NAME = "samples.db"
def get_db_path():
    """Reads the database path from the environment variable."""
    db_path = os.getenv("DB_PATH")
    if not db_path:
        raise ValueError("DB_PATH is not set. Please configure the .env file.")
    return db_path


def check_database_connection():
    """
    Prüft die Verbindung zur Server-Umgebung und Datenbank in der folgenden Reihenfolge:
    1. Ob der Volume-Pfad zugänglich ist (Server zugänglich).
    2. Ob die Datenbankdatei existiert.
    3. Initialisiert die Datenbank, falls sie nicht existiert.
    4. Bestätigt erfolgreiche Verbindung.
    """
    db_path = get_db_path()

    # Sicherstellen, dass die Umgebungsvariable definiert ist
    if not db_path:
        logging.error("❌ DB_PATH is not defined in the environment variables.")
        st.error("❌ Database path (DB_PATH) is not configured. Please check your environment variables.")
        return False

    # 1. Prüfen, ob der Volume-Pfad erreichbar ist (übergeordnetes Verzeichnis des Datenbankpfads)
    volume_path = os.path.dirname(db_path)  # Nur das Verzeichnis ohne Dateinamen
    if not os.path.exists(volume_path):
        logging.error(f"❌ Volume or directory '{volume_path}' does not exist or is not accessible.")
        st.error(
            f"❌ Volume or directory '{volume_path}' is not accessible. Please ensure the server or drive is connected.")
        return False

    # 2. Prüfen, ob die Datenbankdatei existiert
    if not os.path.exists(db_path):
        logging.warning(f"⚠️ Database file '{db_path}' does not exist and needs to be initialized.")
        st.warning(f"⚠️ Database file not found. Initializing a new database file at '{db_path}'.")

        # Initialisieren der Datenbank
        initialize_database()
        return False

    # 3. Datenbank existiert, prüfen ob Verbindung herstellbar + Initialisierung abgeschlossen
    if not is_database_initialized():
        logging.warning(f"⚠️ Database at '{db_path}' exists but is not initialized.")
        st.warning("⚠️ Database found, but it seems to be uninitialized. Please verify the database setup.")
        return False

    # 4. Erfolgreiche Verbindung
    logging.info(f"✅ Connection to the database established successfully at '{db_path}'.")
    st.success("✅ Connection to the database established successfully!")
    return True

def add_user(username, password, role):
    """
    Adds a new user with a hashed password to the database.

    Args:
        username (str): The username.
        password (str): The password in plain text.
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hash the password

    # Encode the hashed password in Base64 to store it as a unique string
    hashed_password_b64 = base64.b64encode(hashed_password).decode('utf-8')

    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Add a new user account
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password_b64, role))
        conn.commit()
        print(f"User '{username}' was added successfully.")
    except sqlite3.IntegrityError:
        print(f"The username '{username}' already exists.")
    except sqlite3.Error as e:
        print(f"Error adding user: {e}")
    finally:
        conn.close()




def initialize_database():
    """Initialisiert die Datenbanktabellen und Standardbenutzer."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # PRAGMA-Anweisung zum Aktivieren von Fremdschlüsseln
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Tabelle: Samples
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            sample_id TEXT PRIMARY KEY,
            sample_type TEXT,
            project TEXT,
            registration_date TEXT,
            sampling_date TEXT,
            sampling_location TEXT,
            sample_condition TEXT,
            responsible_person TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, 
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)

        # Tabelle: CHN
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chn_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id TEXT NOT NULL,
            analysis_date TEXT,
            carbon_percentage REAL,
            hydrogen_percentage REAL,
            nitrogen_percentage REAL,
            FOREIGN KEY (sample_id) REFERENCES samples (sample_id)

        )
        """)

        # Tabelle: Proximate
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eltra_tga_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT NOT NULL,
                Moisture REAL,
                Volatiles_ar REAL,
                Volatiles_db REAL,
                Ash_LTA_ar REAL,
                Ash_LTA_db REAL,
                Ash_HTA_ar REAL,
                Ash_HTA_db REAL,
                Fixed_C_ar REAL,
                FOREIGN KEY (sample_id) REFERENCES samples (sample_id)

        )
        """)

        conn.commit()
        logging.info("Database initialized.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing the database: {e}")
    finally:
        conn.close()

    # Benutzer initialisieren
    initialize_users()


def initialize_users():
    """Initialisiert Standardbenutzer."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # Fremdschlüssel aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        password = "password123"
        # Passwort-Hash für Standardbenutzer
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        print(hashed_password)
        # Base64-codierter Hash
        hashed_password_b64 = base64.b64encode(hashed_password).decode('utf-8')

        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)
        """, ("admin", hashed_password_b64, "admin")) # Gehashtes Passwort speichern

        conn.commit()
        logging.info("Default user 'admin' added.")
    except sqlite3.Error as e:
        logging.error(f"Error adding default users: {e}")
    finally:
        conn.close()


def authenticate_user(username, password):
    """Überprüft die Anmeldedaten."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # Fremdschlüssel aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Passwort für den Benutzer abrufen
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            stored_password_b64 = result[0]  # Gehashtes Passwort aus der Datenbank (als Base64-String)

            # Base64-String zurück in Bytes umwandeln
            stored_password = base64.b64decode(stored_password_b64)
            #print('Stored Password',stored_password)
            # Prüfen, ob das gehashte Passwort korrekt ist
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return True  # Zugriff gewähren

        return False  # Benutzername oder Passwort ist falsch

    except sqlite3.Error as e:
        logging.error(f"Fehler bei der Authentifizierung: {e}")
        return False
    finally:
        conn.close()


def save_sample_data(sample_id, sample_type, project, registration_date, sampling_date, location, condition,
                     responsible):
    """Speichert Probendaten in der Tabelle 'samples', wenn die ID eindeutig ist."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # Tabelle prüfen (nur Debugzweck, optional):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='samples';")
        table_exists = cursor.fetchone()
        if not table_exists:
            logging.warning("Table 'samples' does not exist. Was the database initialized?")
            return False

        # Prüfe, ob die Sample-ID existiert
        cursor.execute("SELECT COUNT(*) FROM samples WHERE sample_id = ?", (sample_id,))
        result = cursor.fetchone()
        logging.debug(f"Checking sample_id: {sample_id}, Query result: {result}")

        if result and result[0] > 0:
            raise sqlite3.IntegrityError(f"Sample ID {sample_id} existiert bereits!")

        # Daten speichern
        cursor.execute("""
            INSERT INTO samples (sample_id, sample_type, project, registration_date, sampling_date, sampling_location, sample_condition, responsible_person)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sample_id, sample_type, project, registration_date, sampling_date, location, condition, responsible))
        conn.commit()
        logging.info(f"Sample with ID '{sample_id}' successfully saved.")
        return True

    except sqlite3.Error as e:
        conn.rollback()  # Rollback falls Fehler
        logging.error(f"Error while saving sample data: {e}", exc_info=True)
        return False


def save_dataframe_to_sql(df, table_name):
    try:
        if df.empty:
            logging.error("Cannot save the DataFrame because it is empty.")
            st.warning("The provided DataFrame is empty and cannot be saved.")
            return  # Beenden, wenn DataFrame leer ist

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fremdschlüssel aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Prüfen, ob die Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise ValueError(f"The table '{table_name}' does not exist in the database.")

        # Abrufen der gültigen sample_id aus der Tabelle 'samples'
        cursor.execute("SELECT CAST(sample_id AS TEXT) FROM samples")
        valid_sample_ids = {row[0] for row in cursor.fetchall()}

        # Beispielhafte Überprüfung: eingehende sample_ids prüfen
        incoming_sample_ids = set(df["sample_id"].astype(str))
        valid_ids = incoming_sample_ids.intersection(valid_sample_ids)
        invalid_ids = incoming_sample_ids.difference(valid_sample_ids)

        # Warnung bei ungültigen sample_ids
        if invalid_ids:
            logging.warning(f"{len(invalid_ids)} invalid sample_id(s) were ignored.")
            warning_message = f"The following sample_id(s) were ignored because they are not registered: {', '.join(invalid_ids)}"
            st.warning(warning_message, icon="⚠️")

        # Nur für CHN-Daten: Überprüfung der Duplikate mit analysis_date
        if "analysis_date" in df.columns and table_name == "chn_data":
            # Vorhandene Kombinationen aus sample_id und analysis_date abrufen
            logging.info(f"analysis Date EXIST")
            cursor.execute(f"SELECT sample_id, analysis_date FROM {table_name}")
            existing_records = cursor.fetchall()
            existing_combinations = {(row[0], row[1]) for row in existing_records}  # Set mit bestehenden Kombinationen

            # Eingehende Kombinationen prüfen
            incoming_combinations = set(zip(df["sample_id"].astype(str), df["analysis_date"].astype(str)))
            duplicate_combinations = incoming_combinations.intersection(existing_combinations)
            new_combinations = incoming_combinations.difference(existing_combinations)

            # Warnung für doppelte Kombinationen von 'sample_id' und 'analysis_date'
        if duplicate_combinations:
            logging.warning(
                f"{len(duplicate_combinations)} duplicate sample_id(s) with the same analysis_date were ignored."
            )
            warning_message = (
                "The following sample_id(s) with the same analysis_date already exist and were ignored: "
                f"{', '.join(f'{x[0]} ({x[1]})' for x in duplicate_combinations)}"
            )
            st.warning(warning_message, icon="⚠️")

        # Filtern der gültigen Datensätze (Basierend auf neuen Kombinationen)
        valid_data = df.loc[df.apply(
            lambda row: (str(row["sample_id"]), str(row["analysis_date"])) in new_combinations, axis=1
        )].copy()

        # Überprüfung, ob gültige Daten vorhanden sind
        if not valid_data.empty:
            # Logging: Anzahl der gültigen Datensätze
            logging.info(f"{len(valid_data)} valid records successfully filtered for saving.")

            # Weiterverarbeitung oder Speicherung der Daten in die Datenbank
            try:
                engine = create_engine(f"sqlite:///{db_path}")
                valid_data.to_sql(name=table_name, con=engine, if_exists="append", index=False)
                logging.info(f"{len(valid_data)} valid records successfully saved to the database.")
            except Exception as e:
                logging.error(f"Error occurred while saving valid data: {e}")
                st.error(f"❌ An error occurred while saving valid records: {e}")

        else:
            # Keine gültigen Datensätze gefunden
            if duplicate_combinations:
                logging.info(
                    "No valid records were found due to duplicate combinations being ignored. Nothing was saved."
                )
            else:
                logging.info("No valid records found in the provided DataFrame. Nothing was saved.")

    except ValueError as ve:
        logging.error(f"Error: {ve}")  # Log ValueErrors
        st.warning(f"A value error occurred: {ve}")
    except sqlite3.Error as se:
        logging.error(f"SQLite Error: {se}")  # Log SQLite errors
        st.warning(f"A database error occurred: {se}")
    except Exception as e:
        logging.error(f"General Error: {e}")  # Catch all other errors
        st.error(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def fetch_all_users():
    """Holt alle Benutzer und Rollen aus der Datenbank."""
    try:
        conn = sqlite3.connect("samples.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        st.error("An error occurred while retrieving the users.")  # Clear, English error message for Streamlit UI
        logging.error("Error while retrieving the users.")  # Detailed backend log entry for developers
        return []
    finally:
        conn.close()


def fetch_all_samples():
    """Returns all samples from the `samples` table."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        query = "SELECT * FROM samples"
        logging.info("Retrieved all samples.")
        # Load the database query directly into a Pandas DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    except sqlite3.Error as e:
        logging.error(f"Error retrieving samples: {e}")
    finally:
        conn.close()


def fetch_all_data(table_name):
    """
    Ruft alle vorhandenen Daten aus einer Tabelle in der Datenbank ab und gibt diese als DataFrame zurück.

    Args:
        table_name (str): Der Name der Tabelle, aus der Daten abgerufen werden sollen.

    Returns:
        pd.DataFrame: Ein DataFrame mit allen Daten aus der Tabelle. Gibt einen leeren DataFrame zurück, falls keine Daten vorhanden sind.
    """
    print(table_name)
    try:
        # Verbindung zur SQLite-Datenbank herstellen
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Fremdschlüssel aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        # SQL-Abfrage für die angegebene Tabelle
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Prüfen, ob Daten vorhanden sind
        if not rows:
            logging.info(f"No data available in the table '{table_name}'.")
            return pd.DataFrame()  # Leerer DataFrame

        # Spaltennamen aus der Tabelle holen
        columns = [desc[0] for desc in cursor.description]

        # Daten in DataFrame umwandeln
        return pd.DataFrame(rows, columns=columns)

    except sqlite3.Error as e:
        logging.error(f"Error retrieving data from '{table_name}': {e}")
        return pd.DataFrame()  # Rückgabe eines leeren DataFrame im Fehlerfall

    finally:
        if conn:
            conn.close()

def check_existing_data(new_data, table_name, id_column="sample_id"):
    """
    Prüft, ob die neuen Daten bereits in der angegebenen Tabelle der Datenbank vorhanden sind.

    Args:
        new_data (pd.DataFrame): Ein DataFrame mit neuen Daten, die eingefügt werden sollen.
        table_name (str): Der Name der Tabelle, in der geprüft werden soll.
        id_column (str): Der Name der Spalte, die die eindeutigen IDs enthält (Standard: "sample_id").

    Returns:
        bool: True, wenn Überschneidungen gefunden wurden (Duplikate), False, wenn keine vorhanden sind.
              Gibt None zurück im Fehlerfall.
    """
    if id_column not in new_data.columns:
        logging.error(f"The column '{id_column}' is missing in the provided data.")
        return None

    existing_ids = set()  # Temporäre Sammlung für bestehende IDs

    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Fremdschlüssel aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Dynamische SQL-Abfrage mit Platzhalter (Tabellenname wird sicher eingefügt)
        query = f"SELECT {id_column} FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Existierende IDs in ein Set konvertieren (für schnelle Suche)
        existing_ids = {row[0] for row in rows}

        # Debug-Logging: Zeige alle abgerufenen IDs
        logging.debug(f"Existing IDs from '{table_name}': {existing_ids}")

    except sqlite3.Error as e:
        logging.error(f"Error retrieving existing data from the table'{table_name}': {e}")
        return None  # Fehlerfall

    finally:
        if conn:
            conn.close()

    # Extrahiere die neuen IDs aus den hochgeladenen Daten
    new_ids = set(new_data[id_column].astype(str))  # IDs als Strings behandeln (Konsistenz)

    # Prüfe auf Überschneidungen
    duplicates = new_ids.intersection(existing_ids)

    if duplicates:
        logging.info(f"Duplicates found: {duplicates}")
        return True  # Überschneidungen existieren

    logging.info("No duplicates found.")
    return False  # Keine Überschneidungen

def is_database_initialized():
    """
    Überprüft, ob die Datenbank initialisiert ist (z. B. Tabellen vorhanden).
    """
    try:
        connection = sqlite3.connect(get_db_path())
        cursor = connection.cursor()

        # Beispiel: Überprüfung, ob die Tabelle 'samples' existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='samples';")
        result = cursor.fetchone()

        return result is not None  # True, wenn Tabelle existiert
    except Exception as e:
        logging.error(f"Error while checking database initialization: {e}")
        return False
    finally:
        connection.close()
