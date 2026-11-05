import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.constants import LEGAL_DISCLAIMER_EN
from app.core.database import init_db

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("legalease_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to run startup and shutdown routines."""
    logger.info("Initializing LegalEase AI backend services...")
    # Auto-initialize database tables (PostgreSQL or SQLite fallback)
    try:
        await init_db()
        logger.info("Database schema verified and initialized.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    yield
    logger.info("Shutting down LegalEase AI backend services...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-oriented Intelligent Legal Decision Support System for Indian citizens.\n\n"
        f"**Statutory Advisory**: {LEGAL_DISCLAIMER_EN}"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint verifying API server status."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "disclaimer": LEGAL_DISCLAIMER_EN,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )
