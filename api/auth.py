"""
Static API key authentication via X-API-Key header.
Key is loaded once at startup from systemd credentials or environment.
"""

from __future__ import annotations
import os
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY: str | None = None

_header_scheme = APIKeyHeader(name='X-API-Key', auto_error=False)


def load_api_key() -> str:
    global _API_KEY
    creds_dir = os.environ.get('CREDENTIALS_DIRECTORY')
    if creds_dir:
        path = os.path.join(creds_dir, 'api_key')
        if os.path.exists(path):
            _API_KEY = open(path).read().strip()
            return _API_KEY
    _API_KEY = os.environ.get('API_KEY', '')
    if not _API_KEY:
        raise RuntimeError('API_KEY not set — provide via systemd credential or API_KEY env var')
    return _API_KEY


def require_api_key(key: str | None = Security(_header_scheme)) -> str:
    if not _API_KEY:
        raise RuntimeError('API key not loaded — call load_api_key() at startup')
    if not key or key != _API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')
    return key
