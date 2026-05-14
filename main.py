import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.database import db_client
from app.api.v1 import triage, doctor, reports, wearables, mental_health, public_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegis_core")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager managing runtime database client pools.
    """
    logger.info("Initializing Aegis Triage OS Lifespan...")
    # Initialize database connection pool
    await db_client.connect()
    yield
    # Shutdown database connection pool
    await db_client.disconnect()
    logger.info("Aegis Triage OS Lifespan terminated.")

app = FastAPI(
    title="Aegis Triage OS",
    description="Advanced AI-driven medical triage and public health monitoring system.",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def add_medical_disclaimer_header(request: Request, call_next):
    """
    Mandatory global middleware interceptor to inject medical disclaimer.
    Every response from the server MUST include the header X-Medical-Disclaimer.
    """
    response: Response = await call_next(request)
    response.headers["X-Medical-Disclaimer"] = (
        "Aegis OS is an AI assistant, not a replacement for professional medical diagnosis."
    )
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global fallback error handling to prevent internal server stack leaks.
    """
    logger.error(f"Internal health engine exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal health engine exception logged safely."}
    )

# Mounting v1 Routers
app.include_router(triage.router, prefix="/api/v1/triage", tags=["Clinical Triage"])
app.include_router(doctor.router, prefix="/api/v1/doctor", tags=["Professional Routing"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Health Reports"])
app.include_router(wearables.router, prefix="/api/v1/wearables", tags=["Vitals Monitoring"])
app.include_router(mental_health.router, prefix="/api/v1/mental", tags=["Psychometric Assessments"])
app.include_router(public_health.router, prefix="/api/v1/public-health", tags=["Epidemic Monitoring"])

@app.get("/health", tags=["System"])
async def health_check():
    """
    System status monitoring endpoint.
    """
    return {"status": "operational", "engine": "Aegis Core"}
