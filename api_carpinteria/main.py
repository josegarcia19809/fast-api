from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal

app = FastAPI(
    title="API de la Carpintería",
    description="Consulta los productos disponibles."
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
