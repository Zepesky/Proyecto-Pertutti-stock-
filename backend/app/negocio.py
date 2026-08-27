"""
Funciones de negocio: todo lo que tiene que ver con la lógica de stock, ventas
y estadísticas (separado de los endpoints para que main.py quede más limpio).
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models

DIAS_PARA_ALERTA = 3


def dias_de_antiguedad(fecha_carga):
    """Cuántos días pasaron desde que se cargó un lote."""
    diferencia = datetime.utcnow() - fecha_carga
    return diferencia.days


def lote_con_alerta(lote):
    """Un lote tiene alerta si tiene más de 3 días Y todavía le queda stock (si ya se vendió todo, no importa)."""
    return dias_de_antiguedad(lote.fecha_carga) > DIAS_PARA_ALERTA and lote.cantidad_actual > 0


def armar_lote_salida(lote):
    """Arma el diccionario de salida de un lote agregando los campos calculados (antigüedad y alerta)."""
    return {
        "id": lote.id,
        "tipo": lote.tipo,
        "tamano": lote.tamano,
        "cantidad_inicial": lote.cantidad_inicial,
        "cantidad_actual": lote.cantidad_actual,
        "fecha_carga": lote.fecha_carga,
        "dias_de_antiguedad": dias_de_antiguedad(lote.fecha_carga),
        "alerta": lote_con_alerta(lote),
    }


def descontar_stock_fifo(db: Session, sucursal_id, tipo, tamano, cantidad_a_vender, usuario_id):
    """
    Descuenta stock del tipo/tamaño pedido, empezando por el lote más viejo
    (FIFO: First In, First Out) ya que es el criterio de rotación que pidió Fabrizio.

    Devuelve la lista de Ventas creadas (puede ser más de una si la venta
    tuvo que "partirse" entre varios lotes), o lanza ValueError si no hay
    stock suficiente.
    """
    lotes_disponibles = (
        db.query(models.Lote)
        .filter(
            models.Lote.sucursal_id == sucursal_id,
            models.Lote.tipo == tipo,
            models.Lote.tamano == tamano,
            models.Lote.cantidad_actual > 0,
        )
        .order_by(models.Lote.fecha_carga.asc())
        .all()
    )

    stock_disponible = sum(lote.cantidad_actual for lote in lotes_disponibles)
    if stock_disponible < cantidad_a_vender:
        raise ValueError(
            "Stock insuficiente. Disponible: " + str(stock_disponible) + ", pedido: " + str(cantidad_a_vender)
        )

    ventas_creadas = []
    cantidad_restante = cantidad_a_vender

    for lote in lotes_disponibles:
        if cantidad_restante <= 0:
            break

        cantidad_de_este_lote = min(lote.cantidad_actual, cantidad_restante)
        lote.cantidad_actual -= cantidad_de_este_lote
        cantidad_restante -= cantidad_de_este_lote

        venta = models.Venta(
            lote_id=lote.id,
            cantidad=cantidad_de_este_lote,
            sucursal_id=sucursal_id,
            usuario_id=usuario_id,
        )
        db.add(venta)
        ventas_creadas.append(venta)

    db.commit()
    for venta in ventas_creadas:
        db.refresh(venta)

    return ventas_creadas


def obtener_stock_resumen(db: Session, sucursal_id):
    """Devuelve el stock actual agrupado por tipo y tamaño (sumando todos los lotes vigentes)."""
    filas = (
        db.query(
            models.Lote.tipo,
            models.Lote.tamano,
            func.sum(models.Lote.cantidad_actual).label("cantidad_total"),
        )
        .filter(models.Lote.sucursal_id == sucursal_id)
        .group_by(models.Lote.tipo, models.Lote.tamano)
        .all()
    )
    return [
        {"tipo": fila.tipo, "tamano": fila.tamano, "cantidad_total": fila.cantidad_total or 0}
        for fila in filas
    ]


def obtener_ventas_por_dia(db: Session, sucursal_id, ultimos_n_dias=30):
    """Total vendido por día, para graficar estadísticas."""
    filas = (
        db.query(
            func.date(models.Venta.fecha).label("dia"),
            func.sum(models.Venta.cantidad).label("cantidad_total"),
        )
        .filter(models.Venta.sucursal_id == sucursal_id)
        .group_by(func.date(models.Venta.fecha))
        .order_by(func.date(models.Venta.fecha).desc())
        .limit(ultimos_n_dias)
        .all()
    )
    return [{"dia": str(fila.dia), "cantidad_total": fila.cantidad_total or 0} for fila in filas]


def obtener_ventas_por_tipo(db: Session, sucursal_id):
    """Total vendido agrupado por tipo y tamaño (para ver qué variante se vende más)."""
    filas = (
        db.query(
            models.Lote.tipo,
            models.Lote.tamano,
            func.sum(models.Venta.cantidad).label("cantidad_total"),
        )
        .join(models.Lote, models.Venta.lote_id == models.Lote.id)
        .filter(models.Venta.sucursal_id == sucursal_id)
        .group_by(models.Lote.tipo, models.Lote.tamano)
        .all()
    )
    return [
        {"tipo": fila.tipo, "tamano": fila.tamano, "cantidad_total": fila.cantidad_total or 0}
        for fila in filas
    ]
