import logging
import json
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.services.database import db_client
from app.api.v1 import triage, doctor, reports, wearables, mental_health, public_health, auth
from app.core.observability import ObservabilityMiddleware, logger
from app.core.auth import check_role

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager managing runtime database client pools.
    """
    logger.info("Initializing Aegis Enterprise Engine...")
    await db_client.connect()
    yield
    await db_client.disconnect()
    logger.info("Aegis Enterprise Engine terminated.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade AI Clinical Triage & Epidemic Monitoring OS",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 1. ENTERPRISE OBSERVABILITY & TRACING
app.add_middleware(ObservabilityMiddleware)

# 2. PII LEAKAGE PREVENTION MIDDLEWARE (Safety Rail)
class PIIMaskingMiddleware(BaseHTTPMiddleware):
    """
    Final safety rail to mask any accidentally leaked PII in response bodies.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.headers.get("content-type") == "application/json":
            # Buffer the response to scan for PII patterns
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Simple regex mask for phones and emails as a final safeguard
            text_body = body.decode()
            text_body = re.sub(r"(?:\+91|0)?[6-9]\d{9}", "[MASKED_PII]", text_body)
            text_body = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[MASKED_PII]", text_body)
            
            return Response(
                content=text_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        return response

app.add_middleware(PIIMaskingMiddleware)

# 3. MEDICAL DISCLAIMER
class MedicalDisclaimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Medical-Disclaimer"] = (
            "Aegis OS is an AI assistant, not a replacement for professional medical diagnosis."
        )
        return response

app.add_middleware(MedicalDisclaimerMiddleware)

# 4. CORS CONFIGURATION
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Medical-Disclaimer", "X-Request-ID", "X-Process-Time-MS"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal enterprise engine error occurred.", "request_id": request.headers.get("X-Request-ID")}
    )

@app.get("/health", tags=["System"])
async def root_health_status():
    return {
        "status": "operational",
        "version": "2.0.0",
        "security": "hardened",
        "observability": "active"
    }

# 5. ENTERPRISE ROUTE MOUNTING
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Security"])
app.include_router(triage.router, prefix="/api/v1/triage", tags=["Clinical Triage"])
app.include_router(
    doctor.router, 
    prefix="/api/v1/doctor", 
    tags=["Professional Routing"],
    dependencies=[Depends(check_role(["DOCTOR", "ADMIN"]))]
)
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Health Reports"])
app.include_router(wearables.router, prefix="/api/v1/wearables", tags=["Vitals Monitoring"])
app.include_router(mental_health.router, prefix="/api/v1/mental", tags=["Psychometric Assessments"])
app.include_router(
    public_health.router, 
    prefix="/api/v1/public-health", 
    tags=["Epidemic Monitoring"],
    dependencies=[Depends(check_role(["ADMIN"]))]
)
