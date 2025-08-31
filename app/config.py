import os
import secrets

class DefaultConfig:
    # Ziel deiner Space2-Instanz (kann in der UI zur Laufzeit überschrieben werden)
    SERVICE_BASE = os.environ.get("SERVICE_BASE", "http://127.0.0.1:5050/space2")

    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "5.0"))

    # Für Flask-Session
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(16)

    # Optionaler Token aus ENV (Fallback, wenn nichts in Session/Datei liegt)
    BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "")

    # Persistenter Speicherort für den Token (einfache Textdatei)
    # Standard: Projektwurzel/bridge_token.txt
    TOKEN_FILE = os.environ.get(
        "TOKEN_FILE",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bridge_token.txt"))
    )
