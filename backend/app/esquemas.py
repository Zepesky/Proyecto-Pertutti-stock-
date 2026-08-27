"""Esquemas (forma de los datos que entran y salen de la API)."""
from pydantic import BaseModel
from datetime import datetime
from app.models import TipoMilanesa, TamanoMilanesa


class LoginEntrada(BaseModel):
    username: str
    password: str


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioSalida(BaseModel):
    id: int
    username: str
    sucursal_id: int

    class Config:
        from_attributes = True


# --- Stock / Lotes ---

class LoteEntrada(BaseModel):
    tipo: TipoMilanesa
    tamano: TamanoMilanesa
    cantidad: int


class LoteSalida(BaseModel):
    id: int
    tipo: TipoMilanesa
    tamano: TamanoMilanesa
    cantidad_inicial: int
    cantidad_actual: int
    fecha_carga: datetime
    dias_de_antiguedad: int
    alerta: bool

    class Config:
        from_attributes = True


class StockResumenItem(BaseModel):
    tipo: TipoMilanesa
    tamano: TamanoMilanesa
    cantidad_total: int


# --- Ventas ---

class VentaEntrada(BaseModel):
    tipo: TipoMilanesa
    tamano: TamanoMilanesa
    cantidad: int


class VentaSalida(BaseModel):
    id: int
    lote_id: int
    cantidad: int
    fecha: datetime

    class Config:
        from_attributes = True


# --- Estadísticas ---

class EstadisticaPorDia(BaseModel):
    dia: str
    cantidad_total: int


class EstadisticaPorTipo(BaseModel):
    tipo: TipoMilanesa
    tamano: TamanoMilanesa
    cantidad_total: int

