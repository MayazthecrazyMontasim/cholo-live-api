import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .database import init_db
from .routers import auth, destinations, budget, trips, chat, organizations, proxy
from .config import ALLOWED_ORIGINS, PROJECT_NAME, PROJECT_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

init_db()

app = FastAPI(
    title=PROJECT_NAME,
    description="REST API for Cholo travel planner — Multi-tenant SaaS",
    version=PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Organization-ID", "X-Workspace-ID", "X-User-ID", "X-User-Role", "X-User-Email"],
)


# ── Security headers ──────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ── Request logging ────────────────────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("%s %s → %s", request.method, request.url.path, response.status_code)
        return response


app.add_middleware(RequestLoggingMiddleware)

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(destinations.router)
app.include_router(budget.router)
app.include_router(trips.router)
app.include_router(chat.router)
app.include_router(organizations.router)
app.include_router(proxy.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to Cholo API! Explore via /docs",
        "version": PROJECT_VERSION,
        "multi_tenant": True,
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "healthy", "service": PROJECT_NAME}
