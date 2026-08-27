# MilaStock — Control de rotación y stock de milanesas

Sistema completo para controlar stock y rotación de milanesas (carne/pollo, grande/infantil)
en una o varias sucursales, con login, alertas de lotes viejos y estadísticas de venta.

👉 **Para arrancar a usarlo, seguí `GUIA_DE_USO.md`.**

## Estructura del proyecto

```
milanesas-app/
├── GUIA_DE_USO.md          ← guía paso a paso para instalar y usar
├── backend/                ← la API (Python + FastAPI)
│   ├── app/
│   │   ├── main.py         ← endpoints de la API
│   │   ├── models.py       ← tablas de la base de datos
│   │   ├── negocio.py      ← lógica de stock/ventas/estadísticas (FIFO, alertas)
│   │   ├── seguridad.py    ← login y tokens
│   │   ├── esquemas.py     ← formas de los datos que entran/salen de la API
│   │   └── database.py     ← conexión a la base de datos
│   ├── crear_datos_prueba.py  ← crea el primer usuario para poder entrar
│   └── requirements.txt
└── frontend/
    └── index.html          ← la app web (funciona en PC y celular)
```

## Funcionalidad incluida

- ✅ Login con usuario y contraseña
- ✅ Carga de stock nuevo (pregunta tipo: carne/pollo, y tamaño: grande/infantil)
- ✅ Carga de venta del día, descuenta automáticamente del stock
- ✅ Descuento por rotación FIFO (siempre se vende primero el lote más viejo)
- ✅ Diferenciación de lotes por fecha de carga
- ✅ Alerta automática cuando un lote supera los 3 días con stock sin vender
- ✅ Estadísticas de venta (por día y por tipo/tamaño)
- ✅ Pensado para varias sucursales usando el sistema a la vez (cada una ve su propio stock)

## Notas técnicas

- Base de datos actual: SQLite (archivo local `milanesas.db`, se crea solo). Para producción
  real con sucursales en distintas ubicaciones físicas, se recomienda pasar a PostgreSQL en
  la nube (por ejemplo Supabase) — solo hay que cambiar `app/database.py`, el resto del
  código no se toca.
- El frontend es una sola página HTML con JavaScript plano (sin frameworks), para que sea
  fácil de abrir y modificar. Funciona igual en PC y celular por ser responsive.
