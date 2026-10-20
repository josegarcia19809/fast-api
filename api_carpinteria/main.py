from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from database import SessionLocal

app = FastAPI(
    title="API de la Carpintería",
    description="Consulta los productos disponibles."
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Directorio donde se guardan las imágenes
BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"

# Crear la carpeta si todavía no existe
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Publicar las imágenes mediante una ruta HTTP
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)


@app.get("/api/productos")
def obtener_productos(db: Session = Depends(get_db)):
    consulta = text("""
                    SELECT id, nombre, material, precio, existencias
                    FROM productos
                    ORDER BY id
                    """)

    resultado = db.execute(consulta).mappings().all()

    return [dict(producto) for producto in resultado]


@app.get("/api/imagenes")
def listar_imagenes():
    extensiones = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    imagenes = [
        {
            "nombre": archivo.name,
            "url": f"/uploads/{archivo.name}",
        }
        for archivo in UPLOADS_DIR.iterdir()
        if archivo.is_file()
           and archivo.suffix.lower() in extensiones
    ]

    return imagenes
