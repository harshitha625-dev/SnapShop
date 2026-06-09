'''"""
backend/main.py — FastAPI app with CLIP + FAISS search
No SerpApi needed. Runs entirely on your local GPU.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import search, upload, catalog
from ml.clip_engine  import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load CLIP + FAISS index once at startup, share across all requests."""
    logger.info("Starting SnapShop — loading CLIP + FAISS…")
    get_engine()          # loads model + index into memory
    logger.info("✅ CLIP + FAISS ready. Server is accepting requests.")
    yield
    logger.info("Shutting down.")


from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="SnapShop — CLIP Visual Search",
    description="Reverse image search powered by CLIP + FAISS. No external APIs.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("data/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")

app.include_router(upload.router,  prefix="/api", tags=["upload"])
app.include_router(search.router,  prefix="/api", tags=["search"])
app.include_router(catalog.router, prefix="/api", tags=["catalog"])


@app.get("/health")
def health():
    engine = get_engine()
    stats  = engine.get_index_stats()
    return {
        "status":       "ok",
        "engine":       "CLIP + FAISS",
        "products":     stats["total_products"],
        "device":       stats["device"],
        "model":        stats["model"],
    }


'''




"""backend/main.py"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers import search, catalog, upload, analyze

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from ml.clip_engine import get_engine
    get_engine()
    yield

app = FastAPI(title="SnapShop Production API", version="3.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Ensure data/uploads exists and serve it under /static
os.makedirs("data/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")

# Include API routers
app.include_router(upload.router,  prefix="/api", tags=["upload"])
app.include_router(search.router,  prefix="/api", tags=["search"])
app.include_router(catalog.router, prefix="/api", tags=["catalog"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])

@app.get("/health")
def health():
    from ml.clip_engine import get_engine
    s = get_engine().get_stats()
    return {"status": "ok", "products": s["total"], "device": s["device"], "model": s["model"]}