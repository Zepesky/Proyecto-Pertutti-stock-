"""
Funciones de seguridad: hashear contraseñas y generar/validar tokens de sesión.

Nunca guardamos la contraseña tal cual en la base de datos, siempre un hash
(una especie de "huella digital" que no se puede revertir a la contraseña original).
"""
from datetime import datetime, timedelta
import os
import bcrypt
from jose import jwt, JWTError

# --- Config del token ---
# La clave secreta se lee de la variable de entorno CLAVE_SECRETA.
# Si no está definida (ej: estás probando en tu compu), usa una de desarrollo.
# EN PRODUCCIÓN ES OBLIGATORIO definir CLAVE_SECRETA en el archivo .env con un
# valor propio, largo y aleatorio — nunca dejar la de desarrollo.
CLAVE_SECRETA = os.environ.get("CLAVE_SECRETA", "clave-de-desarrollo-no-usar-en-produccion")
ALGORITMO = "HS256"
MINUTOS_EXPIRACION_TOKEN = 60 * 8  # el login dura 8 horas antes de pedir de nuevo


def hashear_password(password_plano):
    password_bytes = password_plano.encode("utf-8")
    hash_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password_plano, password_hasheado):
    return bcrypt.checkpw(password_plano.encode("utf-8"), password_hasheado.encode("utf-8"))


def crear_token_acceso(datos):
    a_codificar = datos.copy()
    expira = datetime.utcnow() + timedelta(minutes=MINUTOS_EXPIRACION_TOKEN)
    a_codificar.update({"exp": expira})
    token = jwt.encode(a_codificar, CLAVE_SECRETA, algorithm=ALGORITMO)
    return token


def leer_token(token):
    """Devuelve los datos del token si es válido, o None si es inválido/expiró."""
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        return payload
    except JWTError:
        return None
