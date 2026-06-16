"""
Crypto Trader API Server
========================
FastAPI app serving:
  - REST:    /api/v1/ohlcv, /api/v1/trades, /api/v1/pnl, /api/v1/portfolio
  - GraphQL: /graphql  (POST only; no playground in production)

Auth: X-API-Key header (static key from systemd credential or API_KEY env var)

Run:
  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import load_api_key
from api.db import get_pool, close_pool
from api.routes import router
from api.schema import graphql_router

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_api_key()
    await get_pool()
    log.info('API server started')
    yield
    await close_pool()
    log.info('API server shut down')


app = FastAPI(
    title='Crypto Trader API',
    version='1.0.0',
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET', 'POST'],
    allow_headers=['X-API-Key', 'Content-Type'],
)

app.include_router(router,        prefix='/api/v1')
app.include_router(graphql_router, prefix='/graphql')


@app.get('/health')
async def health():
    return {'status': 'ok'}
