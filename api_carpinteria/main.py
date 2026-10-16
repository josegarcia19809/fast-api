from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

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


@app.get("/api/productos")
def obtener_productos(db: Session = Depends(get_db)):
    consulta = text("""
                    SELECT id, nombre, material, precio, existencias
                    FROM productos
                    ORDER BY id
                    """)

    resultado = db.execute(consulta).mappings().all()

    return [dict(producto) for producto in resultado]
