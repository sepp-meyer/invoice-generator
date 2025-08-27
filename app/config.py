import os
import secrets

class DefaultConfig:
    # Basis deiner bestehenden Space2-App; gern anpassen:
    SERVICE_BASE = os.environ.get("SERVICE_BASE", "http://127.0.0.1:5050/space2")
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "5.0"))

    # Für Flask-Session (wir nutzen sie nur minimal):
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(16)
