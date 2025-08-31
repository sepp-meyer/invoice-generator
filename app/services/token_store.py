import os
from flask import current_app, session, has_request_context

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
    if has_request_context():
        sb = session.get("service_base")
        if sb:
            return sb.strip().rstrip("/")
    return (default_base or "").strip().rstrip("/")

def resolve_token() -> str | None:
    """
    Bevorzugt einheitlich 'api_token' in der Session.
    Akzeptiert legacy 'bridge_token' + ENV-Fallbacks, um Migration zu erleichtern.
    """
    # 1) Request-Session
    if has_request_context():
        t = (session.get("api_token") or "").strip()
        if t:
            return t
        # Legacy Key (falls UI noch nicht aktualisiert war)
        t_legacy = (session.get("bridge_token") or "").strip()
        if t_legacy:
            return t_legacy

    # 2) Persistente Datei
    t = read_persisted_token()
    if t:
        return t.strip()

    # 3) ENV/Config
    t = (current_app.config.get("API_BEARER_TOKEN") or "").strip()
    if t:
        return t
    t = (current_app.config.get("LEGACY_BRIDGE_TOKEN") or "").strip()
    return t or None
