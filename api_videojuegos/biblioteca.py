
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from database import engine

app = FastAPI()


@app.get("/api/autores")
def obtener_autores():
    try:
        with engine.connect() as conexion:
            consulta = text("""
                SELECT id, nombre, apellido
                FROM autor
                ORDER BY apellido, nombre
            """)

            resultado = conexion.execute(consulta)

            autores = [
                dict(fila)
                for fila in resultado.mappings().all()
            ]

            return autores

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar los autores"
        )
