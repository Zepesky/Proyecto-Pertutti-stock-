"""
Configuración de la base de datos.

La conexión se lee de la variable de entorno DATABASE_URL. Si no está
definida, usa SQLite local (para desarrollo/pruebas en tu compu).

En producción (VPS), se define DATABASE_URL en el archivo .env apuntando
a PostgreSQL, y el resto del código (modelos, endpoints) no se toca.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # lee el archivo .env si existe y carga sus variables

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./milanesas.db")

# SQLite necesita este argumento extra; PostgreSQL no.
argumentos_conexion = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=argumentos_conexion)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def obtener_db():
    """Dependencia de FastAPI: abre una sesión de base de datos por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

