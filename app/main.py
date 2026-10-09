from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# Bulk Certificate Generator Backend API

An enterprise-grade, high-performance API for bulk certificate generation.
- **Bulk Job Submission**: Non-blocking asynchronous job queuing (`202 Accepted`).
- **Fault-Tolerant Generation**: Individual recipient failures are isolated without blocking the batch.
- **Dynamic Vector PDF Engine**: Crisp, high-resolution certificates rendered via ReportLab.
- **Live Progress & Status Tracking**: Query status counts (total, processed, successful, failed).
- **Retrieval**: Download individual certificates or a single consolidated ZIP archive.
""",
    lifespan=lifespan
)

# Enable CORS for flexible integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def root_endpoint():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
