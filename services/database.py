import os
import logging
import pandas as pd
import bcrypt
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, ForeignKey, inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.schema import UniqueConstraint

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# .env laden
load_dotenv()

# Versuche zuerst .env, falls leer/nicht vorhanden → nimm st.secrets
DATABASE_URI = os.getenv("DATABASE_URI") or st.secrets.get("DATABASE_URI")

if not DATABASE_URI:
    raise ValueError("❌ DATABASE_URI ist weder in .env noch in st.secrets gesetzt!")

# SQLAlchemy Setup
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    try:
        return Session()
    except SQLAlchemyError as e:
        logging.error(f"❌ Fehler bei Session-Erstellung: {e}")
        return None

def sample_exists(sample_id):
    session = get_session()
    try:
        return session.query(Sample).filter_by(sample_id=sample_id).first() is not None
    finally:
        session.close()
# ORM-Tabellen
class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    password = Column(Text, nullable=False)
    role = Column(String, nullable=False)

class Sample(Base):
    __tablename__ = 'samples'
    sample_id = Column(String, primary_key=True)
    sample_type = Column(String)
    project = Column(String)
    registration_date = Column(String)
    sampling_date = Column(String)
    sampling_location = Column(String)
    sample_condition = Column(String)
    responsible_person = Column(String)


class CHNData(Base):
    __tablename__ = 'chn_data'
    __table_args__ = (UniqueConstraint('sample_id', 'analysis_date', name='uix_sample_analysis'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(String, ForeignKey('samples.sample_id'))
    analysis_date = Column(String)
    carbon_percentage = Column(Float)
    hydrogen_percentage = Column(Float)
    nitrogen_percentage = Column(Float)

class EltraTGAData(Base):
    __tablename__ = 'eltra_tga_data'
    __table_args__ = (UniqueConstraint('sample_id', 'analysis_date', 'moisture', name='uix_sample_analysis_moisture'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(String, ForeignKey('samples.sample_id'))
    analysis_date = Column(String)
    moisture = Column(Float)
    volatiles_ar = Column(Float)
    volatiles_db = Column(Float)
    ash_lta_ar = Column(Float)
    ash_lta_db = Column(Float)
    ash_hta_ar = Column(Float)
    ash_hta_db = Column(Float)
    fixed_c_ar = Column(Float)

# Funktionen
def initialize_database_if_needed():
    """Initialisiert die Datenbank, wenn noch keine Tabellen vorhanden sind."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {'users', 'samples', 'chn_data', 'eltra_tga_data'}

    if not required_tables.issubset(existing_tables):
        initialize_database()
        logging.info("🆕 Datenbank wurde initialisiert.")
        return True  # gibt zurück, dass Initialisierung stattfand
    return False  # war schon vorhanden

def initialize_database():
    try:
        Base.metadata.create_all(engine)
        logging.info("✅ Tabellen erstellt (falls nicht vorhanden).")
    except SQLAlchemyError as e:
        logging.error(f"❌ Fehler beim Erstellen der Tabellen: {e}")

def update_user_role(username, new_role):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            user.role = new_role
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Aktualisieren der Rolle: {e}")
        return False
    finally:
        session.close()

def delete_user(username):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Löschen des Benutzers: {e}")
        return False
    finally:
        session.close()

def initialize_default_users():
    session = get_session()
    try:
        existing = session.query(User).filter_by(username="admin").first()
        if not existing:
            hashed_pw = bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode()
            session.add(User(username="admin", password=hashed_pw, role="admin"))
            session.commit()
            logging.info("✅ Standard-Admin 'admin' wurde erstellt.")
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Initialisieren des Standard-Admins: {e}")
    finally:
        session.close()

def add_user(username, password, role):
    session = get_session()
    try:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        session.add(User(username=username, password=hashed_pw, role=role))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        logging.warning("⚠️ Benutzername existiert bereits.")
        return False
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Hinzufügen des Benutzers: {e}")
        return False
    finally:
        session.close()

def authenticate_user(username, password):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return True, user.role
        return False, None
    except Exception as e:
        logging.error(f"❌ Fehler bei der Authentifizierung: {e}")
        return False, None
    finally:
        session.close()

def fetch_all_users():
    session = get_session()
    try:
        users = session.query(User).all()
        return [(user.username, user.role) for user in users]
    except Exception as e:
        logging.error(f"❌ Fehler beim Laden der Benutzer: {e}")
        return []
    finally:
        session.close()

def save_sample_data(**kwargs):
    session = get_session()
    try:
        session.add(Sample(**kwargs))
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Speichern des Samples: {e}")
        return False
    finally:
        session.close()

def save_dataframe_to_chn_table(df):
    session = get_session()
    success_count = 0
    skipped_count = 0
    error_count = 0
    missing_samples = []

    try:
        for _, row in df.iterrows():
            if not sample_exists(row['sample_id']):
                skipped_count += 1
                missing_samples.append(row['sample_id'])
                continue

            exists = session.query(CHNData).filter_by(
                sample_id=row['sample_id'],
                analysis_date=row['analysis_date']
            ).first()

            if exists:
                skipped_count += 1
                continue

            entry = CHNData(
                sample_id=row['sample_id'],
                analysis_date=row['analysis_date'],
                carbon_percentage=row['carbon_percentage'],
                hydrogen_percentage=row['hydrogen_percentage'],
                nitrogen_percentage=row['nitrogen_percentage']
            )
            session.add(entry)
            success_count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Speichern von CHN-Daten: {e}")
        error_count += 1
    finally:
        session.close()

    return success_count, skipped_count, error_count, missing_samples

def save_dataframe_to_tga_table(df):
    session = get_session()
    success_count = 0
    skipped_count = 0
    error_count = 0
    missing_samples = []

    try:
        for _, row in df.iterrows():
            if not sample_exists(row['sample_id']):
                skipped_count += 1
                missing_samples.append(row['sample_id'])
                continue

            exists = session.query(EltraTGAData).filter_by(
                sample_id=row['sample_id'],
                analysis_date=row['analysis_date'],
                moisture=row['moisture']
            ).first()

            if exists:
                skipped_count += 1
                continue

            entry = EltraTGAData(
                sample_id=row['sample_id'],
                analysis_date=row['analysis_date'],
                moisture=row['moisture'],
                volatiles_ar=row['volatiles_ar'],
                volatiles_db=row['volatiles_db'],
                ash_lta_ar=row['ash_lta_ar'],
                ash_lta_db=row['ash_lta_db'],
                ash_hta_ar=row['ash_hta_ar'],
                ash_hta_db=row['ash_hta_db'],
                fixed_c_ar=row['fixed_c_ar']
            )
            session.add(entry)
            success_count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Fehler beim Speichern der TGA-Daten: {e}")
        error_count += 1
    finally:
        session.close()

    return success_count, skipped_count, error_count, missing_samples

def fetch_all_data(table_class):
    session = get_session()
    try:
        entries = session.query(table_class).all()
        return pd.DataFrame([{k: v for k, v in vars(e).items() if not k.startswith('_')} for e in entries])
    except Exception as e:
        logging.error(f"❌ Fehler beim Laden der Daten aus {table_class.__tablename__}: {e}")
        return pd.DataFrame()
    finally:
        session.close()
