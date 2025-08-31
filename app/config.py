import os
import secrets

class DefaultConfig:
    # Ziel deiner Space2-Instanz
    SERVICE_BASE = os.environ.get("SERVICE_BASE", "http://127.0.0.1:5050/space2")

    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "5.0"))

    # Für Flask-Session
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(16)

    # Einziger, kanonischer Token-Name (für ENV)
    API_BEARER_TOKEN = os.environ.get("API_BEARER_TOKEN", "")

    # Persistenter Speicherort für den Token (einfache Textdatei)
    TOKEN_FILE = os.environ.get(
        "TOKEN_FILE",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bearer_token.txt"))
    )

    # Strikt nur Bridge verwenden
    FORCE_BRIDGE = True
