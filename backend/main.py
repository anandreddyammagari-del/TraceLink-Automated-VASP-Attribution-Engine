import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data
from backend.core.redis_client import cache
from backend.routers.auth_router import router as auth_router
from backend.routers.cases_router import router as cases_router
from backend.routers.transactions_router import router as transactions_router
from backend.routers.traces_router import router as traces_router
from backend.routers.requests_router import router as requests_router
from backend.routers.audit_router import router as audit_router
from backend.routers.sanctions_router import router as sanctions_router
from backend.routers.reports_router import router as reports_router
from backend.routers.websocket_router import router as websocket_router
from backend.routers.analytics_router import router as analytics_router
from backend.routers.victims_router import router as victims_router
from backend.routers.evidence_router import router as evidence_router
from backend.routers.admin_router import router as admin_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tracelink.forensics")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Forensic Workstation Lifespan: DB initialization and seed provisioning."""
    logger.info(f"Initializing {settings.APP_NAME} in {'OFFLINE AIR-GAPPED' if settings.OFFLINE_MODE else 'ONLINE CONNECTED'} mode...")
    
    # Initialize DB schemas
    await init_db()

    # Provision seed data for cyber police officers & cases
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

    # Initialize cache
    await cache.connect()

    # Start trace worker listener
    from backend.workers.trace_worker import start_trace_worker
    await start_trace_worker()

    logger.info(f"TraceLink Forensic Workstation [{settings.WORKSTATION_ID}] Ready.")
    yield
    logger.info("TraceLink Forensic Workstation shutting down gracefully.")

app = FastAPI(
    title="TraceLink — Automated VASP Attribution Engine",
    description="Dedicated Forensic Workstation for State Cyber Police Cells & Law Enforcement Units",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration for Cyber Police Terminal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal police LAN / localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting & Security Headers
from backend.core.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Forensic-Station"] = settings.WORKSTATION_ID
    return response

# Routers
app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(transactions_router)
app.include_router(traces_router)
app.include_router(requests_router)
app.include_router(audit_router)
app.include_router(sanctions_router)
app.include_router(reports_router)
app.include_router(websocket_router)
app.include_router(analytics_router)
app.include_router(victims_router)
app.include_router(evidence_router)
app.include_router(admin_router)

@app.get("/health", tags=["System Diagnostics"])
@app.get("/api/health", tags=["System Diagnostics"])
async def health_check():
    """System health check and forensic integrity report."""
    return {
        "status": "OPERATIONAL",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "workstation_id": settings.WORKSTATION_ID,
        "offline_mode": settings.OFFLINE_MODE,
        "legal_notice": settings.MANDATORY_LEGAL_CAVEAT
    }

@app.get("/health/workers", tags=["System Diagnostics"])
@app.get("/api/health/workers", tags=["System Diagnostics"])
async def worker_health():
    """Diagnostic status for background queue and async forensic workers."""
    from backend.core.kafka_client import event_bus
    from backend.core.redis_client import cache
    queue_size = len(event_bus.in_memory_queue) if hasattr(event_bus, "in_memory_queue") else 0
    return {
        "status": "HEALTHY",
        "workers": {
            "trace_worker": "ACTIVE",
            "watchlist_monitor": "STANDBY",
            "audit_verifier": "ACTIVE"
        },
        "event_bus": {
            "mode": "in_memory" if not event_bus.is_kafka else "kafka",
            "pending_events": queue_size
        },
        "cache": cache.get_stats()
    }

@app.get("/health/system", tags=["System Diagnostics"])
@app.get("/api/health/system", tags=["System Diagnostics"])
async def system_diagnostics():
    """System resource, database, and cache diagnostics."""
    import platform
    import sys
    from backend.core.redis_client import cache
    return {
        "status": "OPERATIONAL",
        "workstation_id": settings.WORKSTATION_ID,
        "os": platform.system(),
        "python_version": sys.version.split()[0],
        "database_backend": "sqlite" if settings.OFFLINE_MODE else "postgresql",
        "cache_stats": cache.get_stats()
    }
