from fastapi import FastAPI

app = FastAPI()

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


# --------------------------------------------------
# 1. Devolver todos los jugadores
# --------------------------------------------------

@app.get("/jugadores")
def obtener_jugadores():
    return jugadores


# --------------------------------------------------
# 2. Filtrar jugadores por posición
# --------------------------------------------------

@app.get("/jugadores/posicion/{posicion}")
def obtener_jugadores_por_posicion(posicion: str):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# --------------------------------------------------
# 3. Obtener cantidad de goles según la posición
# --------------------------------------------------

@app.get("/jugadores/goles/{posicion}")
def obtener_goles(posicion: str):

    total_goles = 0

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            total_goles += jugador["goles"]

    return {
        "posicion": posicion,
        "total_goles": total_goles
    }


# --------------------------------------------------
# 4. Obtener cantidad de jugadores según la posición
# --------------------------------------------------

@app.get("/jugadores/cantidad/{posicion}")
def obtener_cantidad(posicion: str):

    cantidad = 0

    for jugador in jugadores:
        if jugador["posicion"].lower() == posicion.lower():
            cantidad += 1

    return {
        "posicion": posicion,
        "cantidad": cantidad
    }


# --------------------------------------------------
# 5. Obtener promedio de goles según la posición
# --------------------------------------------------

@app.get("/jugadores/promedio/{posicion}")
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

    promedio = total_goles / cantidad

    return {
        "posicion": posicion,
        "promedio": promedio
    }


# --------------------------------------------------
# 6. Buscar un jugador por número
# --------------------------------------------------

@app.get("/jugadores/numero/{numero}")
def obtener_jugador_por_numero(numero: int):

    for jugador in jugadores:
        if jugador["numero"] == numero:
            return jugador

    return {
        "mensaje": "Jugador no encontrado"
    }


# --------------------------------------------------
# 7. Jugadores con más de cierta cantidad de goles
# --------------------------------------------------

@app.get("/jugadores/goles/mayores/{goles}")
def obtener_jugadores_mayores_goles(goles: int):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["goles"] > goles:
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# --------------------------------------------------
# 8. Jugadores con menos de cierta cantidad de goles
# --------------------------------------------------

@app.get("/jugadores/goles/menores/{goles}")
def obtener_jugadores_menores_goles(goles: int):

    jugadores_filtrados = []

    for jugador in jugadores:
        if jugador["goles"] < goles:
            jugadores_filtrados.append(jugador)

    return jugadores_filtrados


# --------------------------------------------------
# 9. Sumar goles de jugadores a partir de un número
# --------------------------------------------------

@app.get("/jugadores/numero/{numero}/goles")
def obtener_goles_desde_numero(numero: int):

    total_goles = 0

    for jugador in jugadores:
        if jugador["numero"] >= numero:
            total_goles += jugador["goles"]

    return {
        "numero": numero,
        "total_goles": total_goles
    }


# --------------------------------------------------
# 10. Contar jugadores que superan una cantidad de goles
# --------------------------------------------------

@app.get("/jugadores/goles/{goles}/cantidad")
def obtener_cantidad_por_goles(goles: int):

    cantidad = 0

    for jugador in jugadores:
        if jugador["goles"] > goles:
            cantidad += 1

    return {
        "goles": goles,
        "cantidad": cantidad
    }


# --------------------------------------------------
# 11. Obtener promedio de goles según el número
# --------------------------------------------------

@app.get("/jugadores/numero/{numero}/promedio")
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

    promedio = total_goles / cantidad

    return {
        "numero": numero,
        "promedio": promedio
    }