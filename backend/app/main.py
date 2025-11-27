"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings, validate_settings
from .services.storage.json_storage import JSONStorage
from .services.storage.sqlite_storage import SQLiteStorage
from .services.storage.postgres_storage import PostgresStorage
from .services.knowledge import KnowledgeBase
from .api import chat

# Validate configuration
validate_settings()

# Initialize storage based on config
if settings.STORAGE_TYPE == "json":
    storage = JSONStorage(settings.DATA_PATH)
elif settings.STORAGE_TYPE == "sqlite":
    db_path = os.path.join(settings.DATA_PATH, "chatbot.db")
    storage = SQLiteStorage(db_path)
elif settings.STORAGE_TYPE == "postgres":
    storage = PostgresStorage(settings.DATABASE_URL)
else:
    raise ValueError(f"Invalid STORAGE_TYPE: {settings.STORAGE_TYPE}")

# Load knowledge base
knowledge_base = KnowledgeBase(settings.KNOWLEDGE_PATH)

# Create FastAPI app
app = FastAPI(
    title="AI Chat Widget",
    description="Universal AI chatbot for any website",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


# Serve widget files
widget_path = os.path.join(os.path.dirname(__file__), "../../widget")
if os.path.exists(widget_path):
    app.mount("/widget", StaticFiles(directory=widget_path), name="widget")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Chat Widget",
        "version": "1.0.0",
        "status": "running",
        "storage": settings.STORAGE_TYPE,
        "ai_model": settings.AI_MODEL,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "storage": settings.STORAGE_TYPE}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
