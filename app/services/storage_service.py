# app/services/storage_service.py
import os
from pathlib import Path
from fastapi import UploadFile

class LocalStorageService:
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, filename_no_ext: str) -> str:
        """
        Guarda el UploadFile en disco con nombre filename_no_ext + su extensión original.
        Retorna la ruta completa.
        """
        # extraemos la extensión (.pdf, .jpg, etc.)
        ext = Path(file.filename).suffix or ".pdf"
        dest_path = self.base_dir / f"{filename_no_ext}{ext}"
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
        return str(dest_path)


