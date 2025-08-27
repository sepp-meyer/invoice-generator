import os

class Config:
    # Basis-Host und Prefix deines Entry-Backends (kannst du per ENV überschreiben)
    ENTRY_HOST = os.getenv("ENTRY_HOST", "http://127.0.0.1:5050")
    SPACE_PREFIX = os.getenv("SPACE_PREFIX", "/space2")
    ENTRY_API_BEARER = os.getenv("ENTRY_API_BEARER", "").strip()
    HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10.0"))
