"""
Async PostgreSQL connection pool.
Credentials come from environment or systemd credentials directory.
"""

from __future__ import annotations
import os
import psycopg_pool
import psycopg.rows

_DB_PASSWORD = None
_pool: psycopg_pool.AsyncConnectionPool | None = None

DB_HOST = os.environ['DB_HOST']
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']


def _get_db_password() -> str:
    global _DB_PASSWORD
    if _DB_PASSWORD:
        return _DB_PASSWORD
    creds_dir = os.environ.get('CREDENTIALS_DIRECTORY')
    if creds_dir:
        path = os.path.join(creds_dir, 'db_password')
        if os.path.exists(path):
            _DB_PASSWORD = open(path).read().strip()
            return _DB_PASSWORD
    _DB_PASSWORD = os.environ['DB_PASSWORD']
    return _DB_PASSWORD


async def get_pool() -> psycopg_pool.AsyncConnectionPool:
    global _pool
    if _pool is None:
        conninfo = (
            f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
            f"user={DB_USER} password={_get_db_password()}"
        )
        _pool = psycopg_pool.AsyncConnectionPool(
            conninfo,
            min_size=1,
            max_size=10,
            kwargs={'row_factory': psycopg.rows.dict_row},
        )
        await _pool.open()
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
