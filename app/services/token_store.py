import os
from flask import current_app, session, has_request_context
from urllib.parse import urlparse, urlunparse

# Nur für echte lokale Entwicklung erlauben wir http:
ALLOW_HTTP_LOCAL = {"127.0.0.1", "localhost", "::1"}

def _build_netloc(u, scheme: str | None = None, drop_default_port: bool = True) -> str:
    """
    Baut den netloc (userinfo@host:port) neu zusammen.
    Entfernt Standard-Ports (80 bei http, 443 bei https), wenn drop_default_port=True.
    """
    scheme_eff = (scheme or u.scheme or "https").lower()

    userinfo = ""
    if u.username:
        userinfo = u.username
        if u.password:
            userinfo += f":{u.password}"
        userinfo += "@"

    host = (u.hostname or "")
    port = u.port

    default_port = 443 if scheme_eff == "https" else 80
    if drop_default_port and (port is None or port == default_port):
        port_part = ""
    else:
        port_part = f":{port}" if port is not None else ""

    return f"{userinfo}{host}{port_part}"

def coerce_https(url: str) -> str:
    """
    Erzwingt https für Nicht-Localhost-Hosts.
    Akzeptiert auch Eingaben ohne Schema (fügt https:// hinzu).
    Entfernt einen trailing Slash im Pfad.
    """
    if not url:
        return ""
    # Schema annehmen, wenn keins explizit angegeben ist
    raw = url if "://" in url else f"https://{url}"
    u = urlparse(raw)

    host = (u.hostname or "").lower()
    scheme = (u.scheme or "https").lower()

    # http -> https, außer bei echter Local-Entwicklung
    if scheme == "http" and host not in ALLOW_HTTP_LOCAL:
        scheme = "https"
        netloc = _build_netloc(u, scheme=scheme, drop_default_port=True)
        u = u._replace(scheme=scheme, netloc=netloc)
    else:
        # Falls bereits https: optional 443 entfernen
        if scheme == "https":
            netloc = _build_netloc(u, scheme=scheme, drop_default_port=True)
            u = u._replace(netloc=netloc)

    # trailing Slash am Pfad weg
    path = (u.path or "").rstrip("/")
    u = u._replace(path=path, params="", query="", fragment="")

    return urlunparse(u)

def _token_file_path() -> str:
    return current_app.config.get("TOKEN_FILE")

def read_persisted_token() -> str | None:
    try:
        path = _token_file_path()
        if not path or not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            tok = f.read().strip()
            return tok or None
    except Exception:
        return None

def write_persisted_token(token: str | None) -> None:
    path = _token_file_path()
    if not path:
        return
    if not token:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token.strip())

def resolve_service_base(default_base: str) -> str:
    # Session-Einstellung hat Vorrang
    raw = None
    if has_request_context():
        sb = (session.get("service_base") or "").strip()
        if sb:
            raw = sb
    # sonst Default aus Config
    if not raw:
        raw = (default_base or "").strip()
    # HTTPS erzwingen (außer localhost)
    return coerce_https(raw)

def resolve_token() -> str | None:
    # 1) Session
    if has_request_context():
        t = (session.get("api_token") or "").strip()
        if t:
            return t
    # 2) Datei
    t = read_persisted_token()
    if t:
        return t.strip()
    # 3) ENV
    t = (current_app.config.get("API_BEARER_TOKEN") or "").strip()
    return t or None
