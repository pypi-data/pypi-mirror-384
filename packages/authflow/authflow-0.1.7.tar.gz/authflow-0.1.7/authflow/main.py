"""Main FastAPI application for AuthFlow backend service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from authflow import setup_auth, AuthFlow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AuthFlow backend service...")
    yield
    # Shutdown
    logger.info("Shutting down AuthFlow backend service...")


# Create FastAPI application
app = FastAPI(
    title="AuthFlow API",
    description="Authentication and authorization service powered by Keycloak",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Setup AuthFlow from environment variables
authflow: AuthFlow = setup_auth(
    app,
    prefix="/api/v1",
    enable_cors=False,  # Disable built-in CORS, we'll handle it manually
    enable_request_logging=True,
)

# Add CORS manually to handle error responses correctly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

logger.info("AuthFlow backend service initialized successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "authflow.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
