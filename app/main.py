import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, products, cart, orders, admin, pages
from app.seed import seed_database

logger = logging.getLogger("uvicorn.error")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager:
    Initializes database schema and ensures idempotent seeding on startup.
    """
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)

    # Idempotent seed for admin user and sample grocery catalog
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as exc:
        logger.error(f"Error during startup database seeding: {exc}")
    finally:
        db.close()

    yield
    logger.info("Shutting down FreshMart application...")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects standard security headers to protect cookies and prevent clickjacking/MIME sniffing.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# Initialize FastAPI application
app = FastAPI(
    title="FreshMart Grocery API",
    description="A complete grocery e-commerce RESTful API and storefront built with FastAPI, SQLAlchemy, and SQLite.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Attach Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Mount Static Files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register Page and API Routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)


# Global Exception Handler to avoid leaking internal tracebacks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please try again later."}
        )
    # Re-raise or let default handler handle page errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please return to the homepage."}
    )
