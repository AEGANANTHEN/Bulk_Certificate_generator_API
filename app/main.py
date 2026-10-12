import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import Base, engine
from app.api.v1.router import api_router

# Lifespan event to initialize database schema
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## 🎓 Bulk Certificate Generator API (AEREO Assessment)

A high-performance, resilient backend API to generate verified certificates in bulk.

### Key Capabilities:
- **Bulk Processing:** Accepts requests with large recipient batches and runs them asynchronously.
- **Fault Isolation:** Individual recipient data errors do not disrupt the rest of the generation job.
- **Dual Export:** High-resolution 300 DPI PNG and print-ready PDF certificates.
- **Cryptographic Verification:** Every certificate contains a unique certificate ID and scannable QR verification code.
- **Batch ZIP Downloads:** One-click download of all successful certificates in a job.
- **Interactive Studio UI:** Live real-time dashboard available at root `/`.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Static and Studio UI
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for liveness / readiness probes."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def serve_dashboard():
    """Serves the interactive Certificate Studio Dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Bulk Certificate Generator API</h1><p>Visit <a href='/docs'>/docs</a> for API docs.</p>")
