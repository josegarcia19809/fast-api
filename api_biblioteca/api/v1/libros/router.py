from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.security import get_current_user

router = APIRouter(prefix="/libros", tags=["libros"])


# Modelo para representar un libro
class Libro(BaseModel):
    titulo: str
    autor: str
    anio: int
    editorial: str


# Lista en memoria
libros = [
    {
        "id": 1,
        "titulo": "Cien años de soledad",
        "autor": "Gabriel García Márquez",
        "anio": 1967,
        "editorial": "Sudamericana"
    },
    {
        "id": 2,
        "titulo": "Don Quijote de la Mancha",
        "autor": "Miguel de Cervantes",
        "anio": 1605,
        "editorial": "Francisco de Robles"
    },
    {
        "id": 3,
        "titulo": "El principito",
        "autor": "Antoine de Saint-Exupéry",
        "anio": 1943,
        "editorial": "Reynal & Hitchcock"
    }
]


# GET /libros
# Consultar todos los libros (público)
@router.get("/")
def obtener_libros():
    return libros


# GET /libros/{id}
# Consultar un libro (público)
@router.get("/{libro_id}")
def obtener_libro(libro_id: int):

    for libro in libros:
        if libro["id"] == libro_id:
            return libro

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Libro no encontrado"
    )


# POST /libros
# Registrar un libro (protegido)
@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_libro(
    libro: Libro,
    user=Depends(get_current_user)
):
    nuevo_id = max(
        (libro["id"] for libro in libros),
        default=0
    ) + 1

    nuevo_libro = {
        "id": nuevo_id,
        **libro.model_dump()
    }

    libros.append(nuevo_libro)

    return nuevo_libro


# PUT /libros/{id}
# Actualizar un libro (protegido)
@router.put("/{libro_id}")
def actualizar_libro(
    libro_id: int,
    libro_actualizado: Libro,
    user=Depends(get_current_user)
):

    for indice, libro in enumerate(libros):
        if libro["id"] == libro_id:

            libros[indice] = {
                "id": libro_id,
                **libro_actualizado.model_dump()
            }

            return libros[indice]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Libro no encontrado"
    )


# DELETE /libros/{id}
# Eliminar un libro (protegido)
@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(
    libro_id: int,
    user=Depends(get_current_user)
):

    for indice, libro in enumerate(libros):
        if libro["id"] == libro_id:
            libros.pop(indice)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Libro no encontrado"
    )