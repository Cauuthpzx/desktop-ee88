"""
MaxHub API Server — FastAPI backend for desktop app.

Cau truc:
    server/
    ├── main.py          <- file nay (entry point)
    ├── config.py        <- doc .env, constants
    ├── database.py      <- DB connection, schema, migrations
    ├── auth.py          <- JWT helpers, get_current_user dependency
    ├── models.py        <- Pydantic request/response models
    └── routes/
        ├── auth_routes.py    <- /api/register, /api/login
        ├── user_routes.py    <- /api/me, /api/me/password
        └── system_routes.py  <- /api/health, /api/version

Chay:
    cd server
    python main.py                           # dev
    uvicorn server.main:app --host 0.0.0.0   # production
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes.auth_routes import router as auth_router
from server.routes.user_routes import router as user_router
from server.routes.system_routes import router as system_router
from server.routes.agent_routes import router as agent_router
from server.routes.upstream_routes import router as upstream_router
from server.routes.group_routes import router as group_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MaxHub API started.")
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="MaxHub API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(system_router)
app.include_router(agent_router)
app.include_router(upstream_router)
app.include_router(group_router)


# ── Dev entry point ───────────────────────────────────────────
if __name__ == "__main__":
    from server.database import init_schema
    init_schema()

    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, workers=4)
