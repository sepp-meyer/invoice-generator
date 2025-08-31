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

