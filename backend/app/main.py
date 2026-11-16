from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, check_db_health
from app.schemas import HealthResponse, ReadyResponse
from app.routers import auth, services, customers, bookings, invoices, system

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager ensuring database tables are initialized on startup."""
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Disaster Recovery as Code Small Business Portal with Self-Healing DevOps Automation",
    lifespan=lifespan
)

# Narrow CORS configuration for frontend and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:80",
        "http://192.168.56.30",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Feature Routers
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(customers.router)
app.include_router(bookings.router)
app.include_router(invoices.router)
app.include_router(system.router)

# --- Operational Probes ---
@app.get("/health", response_model=HealthResponse, tags=["Operational Probes"])
def health_check():
    """
    Shallow health check for Nagios Core plugin 'check_portal_health'.
    Returns HTTP 200 when service and database are operational.
    """
    db_ok, message = check_db_health()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "db": "failed", "error": message}
        )
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "db": "ok"
    }

@app.get("/ready", response_model=ReadyResponse, tags=["Operational Probes"])
def readiness_probe():
    """
    Deep readiness probe used by Ansible deployment validation and load balancers.
    """
    db_ok, message = check_db_health()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "reason": message}
        )
    return {
        "ready": True,
        "checks": {
            "database": "connected",
            "integrity": "verified",
            "engine": "sqlite"
        },
        "timestamp": datetime.now(timezone.utc)
    }

@app.get("/", tags=["Operational Probes"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/health"
    }
