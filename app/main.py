from fastapi import FastAPI
from app.routers.documents import router as documents_router
from app.auth.auth_router import router as auth_router
from app.users.users_router import router as users_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gestión Documental ISO27001")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
app.include_router(users_router, prefix="/users", tags=["Usuarios"])
app.include_router(documents_router, prefix="/documents", tags=["Documentos"])
