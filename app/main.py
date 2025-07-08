from fastapi import FastAPI
from app.routers.documents import router as documents_router

app = FastAPI(title="Gestión Documental ISO27001")

app.include_router(documents_router, prefix="/documents", tags=["Documentos"])
