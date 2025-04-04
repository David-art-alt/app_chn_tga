import logging
import streamlit as st


class StreamlitLoggerHandler(logging.Handler):
    """Custom Logging Handler zur Integration in Streamlit."""

    def emit(self, record):
        log_entry = self.format(record)
        if "logs" not in st.session_state:
            st.session_state["logs"] = []  # Initialisiere Logs, falls nicht vorhanden
        st.session_state["logs"].append(log_entry)


# Logging initialisieren
def setup_logger():
    """Initialisiert das globale Logging."""
    logger = logging.getLogger("streamlit_logger")
    logger.setLevel(logging.INFO)  # Setze das Standard-Log-Level (z. B. INFO)

    # Streamlit-Handler (zum Anzeigen der Logs in der App)
    streamlit_handler = StreamlitLoggerHandler()
    streamlit_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(streamlit_handler)

    return logger  # Gibt den Logger zurück

