from fastapi import FastAPI
from typing import Optional

app = FastAPI()


@app.get("/libros")
def obtener_libros(pagina: int = 1, cantidad: int = 10):
    return {
        "pagina": pagina,
        "cantidad": cantidad
    }


@app.get("/libros/opcional")
def obtener_libros_opcional(
        pagina: int = 1,
        cantidad: Optional[int] = None
):
    return {
        "pagina": pagina,
        "cantidad": cantidad
    }


@app.get("/categorias/{nombre_categoria}/libros")
def obtener_libros(
        nombre_categoria: str,
        pagina: int = 1,
        cantidad: int = 10
):
    return {
        "categoria": nombre_categoria,
        "pagina": pagina,
        "cantidad": cantidad
    }
