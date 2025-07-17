from fastapi import FastAPI
from app.routers.documents import router as documents_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gestión Documental ISO27001")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(documents_router, prefix="/documents", tags=["Documentos"])
