import os

class Config:
    # Bitte in Produktion per ENV setzen!
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-please")

    # Upstream deines EntryFrame/Space2-Backends:
    # Standard: http://127.0.0.1:5050/space2
    SERVICE_BASE = os.environ.get("SERVICE_BASE", "http://127.0.0.1:5050/space2")

    # Requests-Timeout in Sekunden
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "6.0"))
