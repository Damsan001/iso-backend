from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "clave_secreta"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30


def crear_token(usuario_id: int, rol: str):
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def crear_token_temporal(usuario_id: int):
    payload = {"sub": usuario_id, "exp": datetime.utcnow() + timedelta(minutes=15)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token_temporal(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
