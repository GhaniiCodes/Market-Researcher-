from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

from api.routes import query_router, history_router
from api.database import init_db
from config.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Validate settings and initialize database
    try:
        settings.validate()
    except EnvironmentError as e:
        raise RuntimeError(f"Configuration error: {str(e)}. Please set required environment variables.")
    init_db()
    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(
    title="AI Research Assistant API",
    description="Multi-agent AI system for news, market research, and stock analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query_router, prefix="/api/v1", tags=["queries"])
app.include_router(history_router, prefix="/api/v1", tags=["history"])

@app.get("/")
async def root():
    return {
        "message": "AI Research Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/v1/query",
            "history": "/api/v1/history",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Research Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)