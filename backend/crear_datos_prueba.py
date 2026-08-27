"""
Script para crear una sucursal y un usuario de prueba, así podés probar el login.

Ejecutar una sola vez con: python crear_datos_prueba.py
"""
from app.database import SessionLocal, engine, Base
from app import models, seguridad

Base.metadata.create_all(bind=engine)

db = SessionLocal()

nombre_sucursal = "Local Principal"
sucursal = db.query(models.Sucursal).filter(models.Sucursal.nombre == nombre_sucursal).first()
if sucursal is None:
    sucursal = models.Sucursal(nombre=nombre_sucursal)
    db.add(sucursal)
    db.commit()
    db.refresh(sucursal)
    print("Sucursal creada:", sucursal.nombre)
else:
    print("La sucursal ya existía:", sucursal.nombre)

username_prueba = "admin"
password_prueba = "admin123"

usuario = db.query(models.Usuario).filter(models.Usuario.username == username_prueba).first()
if usuario is None:
    usuario = models.Usuario(
        username=username_prueba,
        password_hash=seguridad.hashear_password(password_prueba),
        sucursal_id=sucursal.id,
    )
    db.add(usuario)
    db.commit()
    print("Usuario creado -> username:", username_prueba, "| password:", password_prueba)
else:
    print("El usuario ya existía:", username_prueba)

db.close()
