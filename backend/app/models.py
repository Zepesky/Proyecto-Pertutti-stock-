"""
Modelos (tablas) de la base de datos.

Estructura pensada para varias sucursales usando el sistema al mismo tiempo:
cada Sucursal tiene sus propios usuarios, lotes de stock y ventas.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TipoMilanesa(str, enum.Enum):
    carne = "carne"
    pollo = "pollo"


class TamanoMilanesa(str, enum.Enum):
    grande = "grande"
    infantil = "infantil"


class Sucursal(Base):
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="sucursal")
    lotes = relationship("Lote", back_populates="sucursal")
    ventas = relationship("Venta", back_populates="sucursal")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)

    sucursal = relationship("Sucursal", back_populates="usuarios")


class Lote(Base):
    """
    Un lote es una carga de stock: se hicieron X milanesas de un tipo y tamaño
    determinado, en una fecha determinada. La cantidad_actual se va descontando
    a medida que se cargan ventas contra este lote.
    """
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoMilanesa), nullable=False)
    tamano = Column(Enum(TamanoMilanesa), nullable=False)
    cantidad_inicial = Column(Integer, nullable=False)
    cantidad_actual = Column(Integer, nullable=False)
    fecha_carga = Column(DateTime, default=datetime.utcnow, nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)

    sucursal = relationship("Sucursal", back_populates="lotes")
    ventas = relationship("Venta", back_populates="lote")


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    lote = relationship("Lote", back_populates="ventas")
    sucursal = relationship("Sucursal", back_populates="ventas")
    usuario = relationship("Usuario")
