from enum import Enum
from fastapi import FastAPI, Response, status
from typing import Optional

app = FastAPI()


class Genero(str, Enum):
    ACCION = "accion"
    COMEDIA = "comedia"
    CIENCIA_FICCION = "ciencia-ficcion"
    DRAMA = "drama"


peliculas = [
    {
        "id": 1,
        "titulo": "Interestelar",
        "genero": "ciencia-ficcion",
        "plataforma": "Netflix",
        "anio": 2014
    },
    {
        "id": 2,
        "titulo": "Spider-Man",
        "genero": "accion",
        "plataforma": "Disney+",
        "anio": 2021
    },
    {
        "id": 3,
        "titulo": "Intensamente",
        "genero": "comedia",
        "plataforma": "Disney+",
        "anio": 2015
    },
    {
        "id": 4,
        "titulo": "En busca de la felicidad",
        "genero": "drama",
        "plataforma": "Netflix",
        "anio": 2006
    },
    {
        "id": 5,
        "titulo": "Matrix",
        "genero": "ciencia-ficcion",
        "plataforma": "Max",
        "anio": 1999
    },
    {
        "id": 6,
        "titulo": "Avengers: Endgame",
        "genero": "accion",
        "plataforma": "Disney+",
        "anio": 2019
    },
    {
        "id": 7,
        "titulo": "Son como niños",
        "genero": "comedia",
        "plataforma": "Netflix",
        "anio": 2010
    },
    {
        "id": 8,
        "titulo": "Titanic",
        "genero": "drama",
        "plataforma": "Disney+",
        "anio": 1997
    },
    {
        "id": 9,
        "titulo": "Jurassic Park",
        "genero": "ciencia-ficcion",
        "plataforma": "Max",
        "anio": 1993
    },
    {
        "id": 10,
        "titulo": "John Wick",
        "genero": "accion",
        "plataforma": "Prime Video",
        "anio": 2014
    },
    {
        "id": 11,
        "titulo": "Shrek",
        "genero": "comedia",
        "plataforma": "Netflix",
        "anio": 2001
    },
    {
        "id": 12,
        "titulo": "Forrest Gump",
        "genero": "drama",
        "plataforma": "Paramount+",
        "anio": 1994
    },
    {
        "id": 13,
        "titulo": "Avatar",
        "genero": "ciencia-ficcion",
        "plataforma": "Disney+",
        "anio": 2009
    },
    {
        "id": 14,
        "titulo": "Deadpool",
        "genero": "accion",
        "plataforma": "Disney+",
        "anio": 2016
    },
    {
        "id": 15,
        "titulo": "La máscara",
        "genero": "comedia",
        "plataforma": "Prime Video",
        "anio": 1994
    }
]


# 1. Obtener todas las películas
@app.get("/peliculas",
         status_code=status.HTTP_200_OK
         )
def obtener_peliculas(
        genero: Optional[Genero] = None,
        plataforma: Optional[str] = None
):
    resultados = peliculas

    if genero is not None:
        resultados = [
            pelicula for pelicula in resultados
            if pelicula["genero"] == genero.value
        ]

    if plataforma is not None:
        resultados = [
            pelicula for pelicula in resultados
            if pelicula["plataforma"].lower() == plataforma.lower()
        ]

    return resultados


# 2. Buscar películas por género
@app.get("/peliculas/generos/{genero}", status_code=status.HTTP_200_OK)
def peliculas_por_genero(genero: Genero):
    resultados = [
        pelicula
        for pelicula in peliculas
        if pelicula["genero"] == genero.value
    ]

    return resultados


# 3. Buscar películas por año
@app.get("/peliculas/anio/{anio}")
def peliculas_por_anio(anio: int):
    resultados = [
        pelicula
        for pelicula in peliculas
        if pelicula["anio"] == anio
    ]

    return resultados


# 4. Buscar películas por plataforma
@app.get("/peliculas/plataforma/{plataforma}")
def peliculas_por_plataforma(plataforma: str):
    resultados = [
        pelicula
        for pelicula in peliculas
        if pelicula["plataforma"].lower() == plataforma.lower()
    ]

    return resultados


# 5. Obtener películas posteriores a un año
@app.get("/peliculas/desde/{anio}")
def peliculas_desde(anio: int):
    resultados = [
        pelicula
        for pelicula in peliculas
        if pelicula["anio"] >= anio
    ]

    return resultados


# 6. Obtener una película por ID
@app.get("/peliculas/{id}", status_code=status.HTTP_404_NOT_FOUND)
def obtener_pelicula(id: int, response: Response):
    for pelicula in peliculas:
        if pelicula["id"] == id:
            response.status_code = status.HTTP_200_OK
            return pelicula

    return {
        "mensaje": "Película no encontrada"
    }
