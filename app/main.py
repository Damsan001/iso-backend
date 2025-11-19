from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routers.documents import router as documents_router
from app.routers.auth import router as auth_router
from app.users.users_router import router as users_router
from app.routers.reports import router as reports_router
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.infrastructure.db import engine
from app.routers.catalogs import router as catalogs_router
from app.routers.assets import router as assets_router
from app.routers.admin import router as admin_router
from app.users.users_router import router as users_router
from contextlib import asynccontextmanager
from app.routers.risk_router import router as risk_router
from app.routers.treatment_router import router as treatment_router

@asynccontextmanager
async def lifespan(app):
    import app.infrastructure.audit
    yield
app = FastAPI(title="Gestión Documental ISO27001", lifespan=lifespan)



ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://appiso.insaight.com.mx",
    "https://appisoqa.insaight.com.mx",
    "https://iso-frontend-9479.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "x-company-id"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
# app.include_router(users_router, prefix="/users", tags=["Usuarios"])
app.include_router(users_router, prefix="/users", tags=["Usuarios"])
app.include_router(documents_router, prefix="/documents", tags=["Documentos"])
app.include_router(reports_router, prefix="/reports", tags=["Reportes"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(risk_router, prefix="/risks", tags=["Riesgos"])
app.include_router(risk_router, prefix="/riesgos", tags=["Riesgos"])

app.include_router(treatment_router, prefix="/treatments", tags=["Tratamientos"])
app.include_router(treatment_router, prefix="/tratamientos", tags=["Tratamientos"])


# Routers con prefijos locales
# app.include_router(auth_router,      prefix="/auth",      tags=["Autenticación"])
# app.include_router(users_router,     prefix="/users",     tags=["Usuarios"])
# app.include_router(documents_router, prefix="/documents", tags=["Documentos"])
# app.include_router(reports_router,   prefix="/reports",   tags=["Reportes"])

app.include_router(catalogs_router)
app.include_router(assets_router)


@app.get("/", tags=["Health"])
def root():
    return {"ok": True, "service": "ISO27001 API (clean)"}


@app.get("/health/db", tags=["Health"])
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"db": "ok"}


@app.get("/health/dbinfo", tags=["Health"])
def health_dbinfo():
    url = engine.url
    safe_url = f"{url.get_backend_name()}+{url.get_driver_name()}://{url.username}@{url.host}:{url.port}/{url.database}"
    with engine.connect() as conn:
        meta = conn.execute(text("SELECT current_database(), current_schema(), session_user")).first()
        search_path = conn.execute(text("SHOW search_path")).scalar()
        exists = conn.execute(text(
            "SELECT to_regclass('iso.catalog'), to_regclass('iso.catalog_item'), to_regclass('iso.activo')")).first()
    return {
        "engine_url": safe_url,
        "database": meta[0],
        "schema": meta[1],
        "user": meta[2],
        "search_path": search_path,
        "tables_exist": {
            "iso.catalog": bool(exists[0]),
            "iso.catalog_item": bool(exists[1]),
            "iso.activo": bool(exists[2]),
        },
    }
