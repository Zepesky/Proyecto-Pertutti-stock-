"""
Punto de entrada de la API.

Incluye: login, endpoints de stock (cargar lote, ver stock, ver alertas de
lotes viejos), endpoints de ventas (cargar venta con descuento FIFO del
stock) y endpoints de estadísticas.
"""
import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import engine, Base, obtener_db
from app import models, esquemas, seguridad, negocio

# Crea las tablas en la base de datos si todavía no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Control de Stock - Milanesas")

# Aviso en el log si en producción se está usando la clave secreta de desarrollo.
if seguridad.CLAVE_SECRETA == "clave-de-desarrollo-no-usar-en-produccion":
    print("⚠️  ATENCIÓN: estás usando la CLAVE_SECRETA de desarrollo. "
          "Definí la variable de entorno CLAVE_SECRETA con un valor propio antes de ir a producción.")

# Orígenes permitidos para CORS: en producción se define ORIGENES_PERMITIDOS
# en el .env con el dominio real (ej: "https://stock.pertutti.com.ar"),
# separados por coma si hay más de uno. Si no está definida, permite todo
# (cómodo para desarrollo local, pero no recomendado en producción).
origenes = os.environ.get("ORIGENES_PERMITIDOS", "*")
lista_origenes = ["*"] if origenes == "*" else [o.strip() for o in origenes.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=lista_origenes,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(obtener_db)):
    """
    Dependencia para usar en cualquier endpoint que requiera estar logueado.
    Uso: def mi_endpoint(usuario: Usuario = Depends(usuario_actual)): ...
    """
    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )
    datos = seguridad.leer_token(token)
    if datos is None:
        raise error_credenciales

    usuario = db.query(models.Usuario).filter(models.Usuario.id == datos.get("usuario_id")).first()
    if usuario is None:
        raise error_credenciales
    return usuario


@app.post("/login", response_model=esquemas.TokenSalida)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(obtener_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.username == form.username).first()

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos",
    )

    if usuario is None:
        raise credenciales_invalidas
    if not seguridad.verificar_password(form.password, usuario.password_hash):
        raise credenciales_invalidas

    token = seguridad.crear_token_acceso({
        "sub": usuario.username,
        "usuario_id": usuario.id,
        "sucursal_id": usuario.sucursal_id,
    })
    return esquemas.TokenSalida(access_token=token)


@app.get("/")
def raiz():
    return {"mensaje": "API de control de stock de milanesas funcionando"}


@app.get("/yo", response_model=esquemas.UsuarioSalida)
def yo(usuario: models.Usuario = Depends(usuario_actual)):
    """Endpoint de prueba: devuelve los datos del usuario logueado."""
    return usuario


# ==================== STOCK / LOTES ====================

@app.post("/lotes", response_model=esquemas.LoteSalida)
def cargar_lote(
    datos: esquemas.LoteEntrada,
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    """Carga un lote nuevo de stock (se acaban de hacer X milanesas de tal tipo/tamaño)."""
    lote = models.Lote(
        tipo=datos.tipo,
        tamano=datos.tamano,
        cantidad_inicial=datos.cantidad,
        cantidad_actual=datos.cantidad,
        sucursal_id=usuario.sucursal_id,
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return negocio.armar_lote_salida(lote)


@app.get("/lotes", response_model=List[esquemas.LoteSalida])
def listar_lotes(
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    """Lista todos los lotes de la sucursal (incluye los que ya se agotaron)."""
    lotes = (
        db.query(models.Lote)
        .filter(models.Lote.sucursal_id == usuario.sucursal_id)
        .order_by(models.Lote.fecha_carga.desc())
        .all()
    )
    return [negocio.armar_lote_salida(lote) for lote in lotes]


@app.get("/lotes/alertas", response_model=List[esquemas.LoteSalida])
def listar_alertas(
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    """Lista solo los lotes con más de 3 días de antigüedad que todavía tienen stock."""
    lotes = (
        db.query(models.Lote)
        .filter(models.Lote.sucursal_id == usuario.sucursal_id, models.Lote.cantidad_actual > 0)
        .all()
    )
    lotes_con_alerta = [lote for lote in lotes if negocio.lote_con_alerta(lote)]
    return [negocio.armar_lote_salida(lote) for lote in lotes_con_alerta]


@app.get("/stock/resumen", response_model=List[esquemas.StockResumenItem])
def stock_resumen(
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    """Stock actual total, agrupado por tipo y tamaño."""
    return negocio.obtener_stock_resumen(db, usuario.sucursal_id)


# ==================== VENTAS ====================

@app.post("/ventas", response_model=List[esquemas.VentaSalida])
def cargar_venta(
    datos: esquemas.VentaEntrada,
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    """
    Carga la venta del día para un tipo/tamaño determinado. Descuenta del
    stock automáticamente empezando por el lote más viejo (rotación FIFO).
    """
    try:
        ventas = negocio.descontar_stock_fifo(
            db,
            sucursal_id=usuario.sucursal_id,
            tipo=datos.tipo,
            tamano=datos.tamano,
            cantidad_a_vender=datos.cantidad,
            usuario_id=usuario.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return ventas


# ==================== ESTADÍSTICAS ====================

@app.get("/estadisticas/por-dia", response_model=List[esquemas.EstadisticaPorDia])
def estadisticas_por_dia(
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    return negocio.obtener_ventas_por_dia(db, usuario.sucursal_id)


@app.get("/estadisticas/por-tipo", response_model=List[esquemas.EstadisticaPorTipo])
def estadisticas_por_tipo(
    usuario: models.Usuario = Depends(usuario_actual),
    db: Session = Depends(obtener_db),
):
    return negocio.obtener_ventas_por_tipo(db, usuario.sucursal_id)
