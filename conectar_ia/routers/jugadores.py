
from fastapi import APIRouter, HTTPException, status

router = APIRouter(
    prefix="/jugadores",
    tags=["jugadores"]
)


# Lista en memoria
jugadores = [
    {"numero": 1, "nombre": "Lionel Messi", "posicion": "Delantero", "goles": 10},
    {"numero": 9, "nombre": "Cristiano Ronaldo", "posicion": "Delantero", "goles": 12},
    {"numero": 10, "nombre": "Neymar Jr.", "posicion": "Delantero", "goles": 8},
    {"numero": 7, "nombre": "Kylian Mbappé", "posicion": "Delantero", "goles": 9},
    {"numero": 8, "nombre": "Kevin De Bruyne", "posicion": "Mediocampista", "goles": 5},
    {"numero": 6, "nombre": "Luka Modric", "posicion": "Mediocampista", "goles": 13},
    {"numero": 5, "nombre": "N'Golo Kanté", "posicion": "Mediocampista", "goles": 2},
    {"numero": 14, "nombre": "Frenkie de Jong", "posicion": "Mediocampista", "goles": 4},
    {"numero": 20, "nombre": "Toni Kroos", "posicion": "Mediocampista", "goles": 4},
    {"numero": 4, "nombre": "Virgil van Dijk", "posicion": "Defensor", "goles": 1},
    {"numero": 3, "nombre": "Sergio Ramos", "posicion": "Defensor", "goles": 2},
    {"numero": 22, "nombre": "Marquinhos", "posicion": "Defensor", "goles": 1}
]


# GET /jugadores/
# 1. Devolver todos los jugadores
@router.get("/")
def obtener_jugadores():
    return jugadores


# GET /jugadores/posicion/{posicion}
# 2. Filtrar jugadores por posición
@router.get("/posicion/{posicion}")
def obtener_jugadores_por_posicion(posicion: str):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# GET /jugadores/goles/{posicion}
# 3. Obtener cantidad de goles según la posición
@router.get("/goles/{posicion}")
def obtener_goles(posicion: str):

    total_goles = 0

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            total_goles += jugador["goles"]

    return {
        "posicion": posicion,
        "total_goles": total_goles
    }


# GET /jugadores/cantidad/{posicion}
# 4. Obtener cantidad de jugadores según la posición
@router.get("/cantidad/{posicion}")
def obtener_cantidad(posicion: str):

    cantidad = 0

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            cantidad += 1

    return {
        "posicion": posicion,
        "cantidad": cantidad
    }


# GET /jugadores/promedio/{posicion}
# 5. Obtener promedio de goles según la posición
@router.get("/promedio/{posicion}")
def obtener_promedio(posicion: str):

    total_goles = 0
    cantidad = 0

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            total_goles += jugador["goles"]
            cantidad += 1

    if cantidad == 0:
        return {
            "posicion": posicion,
            "promedio": 0
        }

    return {
        "posicion": posicion,
        "promedio": total_goles / cantidad
    }


# GET /jugadores/numero/{numero}
# 6. Buscar un jugador por número
@router.get("/numero/{numero}")
def obtener_jugador_por_numero(numero: int):

    for jugador in jugadores:
        if jugador["numero"] == numero:
            return jugador

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Jugador no encontrado"
    )


# GET /jugadores/goles/mayores/{goles}
# 7. Jugadores con más de cierta cantidad de goles
@router.get("/goles/mayores/{goles}")
def obtener_jugadores_mayores_goles(goles: int):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["goles"] > goles:
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# GET /jugadores/goles/menores/{goles}
# 8. Jugadores con menos de cierta cantidad de goles
@router.get("/goles/menores/{goles}")
def obtener_jugadores_menores_goles(goles: int):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["goles"] < goles:
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# GET /jugadores/numero/{numero}/goles
# 9. Sumar goles de jugadores a partir de un número
@router.get("/numero/{numero}/goles")
def obtener_goles_desde_numero(numero: int):

    total_goles = 0

    for jugador in jugadores:
        if jugador["numero"] >= numero:
            total_goles += jugador["goles"]

    return {
        "numero": numero,
        "total_goles": total_goles
    }


# GET /jugadores/goles/{goles}/cantidad
# 10. Contar jugadores que superan una cantidad de goles
@router.get("/goles/{goles}/cantidad")
def obtener_cantidad_por_goles(goles: int):

    cantidad = 0

    for jugador in jugadores:
        if jugador["goles"] > goles:
            cantidad += 1

    return {
        "goles": goles,
        "cantidad": cantidad
    }


# GET /jugadores/numero/{numero}/promedio
# 11. Obtener promedio de goles según el número
@router.get("/numero/{numero}/promedio")
def obtener_promedio_desde_numero(numero: int):

    total_goles = 0
    cantidad = 0

    for jugador in jugadores:
        if jugador["numero"] > numero:
            total_goles += jugador["goles"]
            cantidad += 1

    if cantidad == 0:
        return {
            "numero": numero,
            "promedio": 0
        }

    return {
        "numero": numero,
        "promedio": total_goles / cantidad
    }
