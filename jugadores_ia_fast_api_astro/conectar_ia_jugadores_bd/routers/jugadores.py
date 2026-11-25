from fastapi import APIRouter, HTTPException, Query
from mysql.connector import Error as MySQLError

from routers import chat_tools as consultas

router = APIRouter(prefix="/jugadores", tags=["jugadores"])


def _ejecutar(funcion, *args):
    try:
        return funcion(*args)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al acceder a MySQL.") from error


@router.get("/")
def obtener_jugadores():
    """Lista los jugadores registrados con los datos disponibles y su club."""
    return _ejecutar(consultas.consultar_jugadores)


@router.get("/buscar")
def buscar_jugador(nombre: str = Query(..., min_length=1, max_length=100)):
    return _ejecutar(consultas.buscar_jugador, nombre)


@router.get("/imagen")
def obtener_imagen_jugador(nombre: str = Query(..., min_length=1, max_length=100)):
    return _ejecutar(consultas.obtener_imagen_jugador, nombre)


@router.get("/por-edad")
def jugadores_por_edad(edad_minima: int = Query(..., ge=0, le=120), edad_maxima: int = Query(..., ge=0, le=120)):
    return _ejecutar(consultas.consultar_jugadores_por_edad, edad_minima, edad_maxima)


@router.get("/por-numero/{numero}")
def jugadores_por_numero(numero: int):
    return _ejecutar(consultas.consultar_jugadores_por_numero, numero)


@router.get("/ordenados")
def jugadores_ordenados(criterio: str = Query(..., min_length=1, max_length=30)):
    return _ejecutar(consultas.consultar_jugadores_ordenados, criterio)


@router.get("/por-nacionalidad/{nacionalidad}")
def jugadores_por_nacionalidad(nacionalidad: str):
    return _ejecutar(consultas.consultar_por_nacionalidad, nacionalidad)


@router.get("/nacionalidades")
def nacionalidades():
    return _ejecutar(consultas.consultar_nacionalidades)


@router.get("/por-posicion/{posicion}")
def jugadores_por_posicion(posicion: str):
    return _ejecutar(consultas.consultar_por_posicion, posicion)


@router.get("/cantidad-por-posicion")
def cantidad_por_posicion():
    return _ejecutar(consultas.consultar_cantidad_por_posicion)


@router.get("/promedio-edad-por-posicion")
def promedio_edad_por_posicion():
    return _ejecutar(consultas.consultar_promedio_edad_por_posicion)


@router.get("/mas-alto")
def jugador_mas_alto():
    return _ejecutar(consultas.consultar_jugador_mas_alto)


@router.get("/mas-bajo")
def jugador_mas_bajo():
    return _ejecutar(consultas.consultar_jugador_mas_bajo)


@router.get("/mas-pesado")
def jugador_mas_pesado():
    return _ejecutar(consultas.consultar_jugador_mas_pesado)


@router.get("/promedios-fisicos")
def promedios_fisicos():
    return _ejecutar(consultas.consultar_promedios_fisicos)


@router.get("/por-pie/{pie}")
def jugadores_por_pie(pie: str):
    return _ejecutar(consultas.consultar_por_pie_dominante, pie)


@router.get("/mas-valioso")
def jugador_mas_valioso():
    return _ejecutar(consultas.consultar_jugador_mas_valioso)


@router.get("/menos-valioso")
def jugador_menos_valioso():
    return _ejecutar(consultas.consultar_jugador_menos_valioso)


@router.get("/valor-mercado/total")
def valor_total_mercado():
    return _ejecutar(consultas.consultar_valor_total_mercado)


@router.get("/valor-mercado/promedio")
def promedio_valor_mercado():
    return _ejecutar(consultas.consultar_promedio_valor_mercado)


@router.get("/por-valor")
def jugadores_por_valor(valor_minimo: float = Query(..., ge=0), valor_maximo: float = Query(..., ge=0)):
    return _ejecutar(consultas.consultar_jugadores_por_valor, valor_minimo, valor_maximo)


@router.get("/valor-mercado/por-nacionalidad")
def valor_mercado_por_nacionalidad():
    return _ejecutar(consultas.consultar_valor_mercado_por_nacionalidad)


@router.get("/estadisticas")
def estadisticas_jugadores():
    return _ejecutar(consultas.consultar_estadisticas_jugadores)


@router.get("/por-club/{club}")
def jugadores_por_club(club: str, posicion: str | None = None):
    return _ejecutar(consultas.consultar_jugadores_por_club, club, posicion or "")


@router.get("/por-liga/{liga}")
def jugadores_por_liga(liga: str):
    return _ejecutar(consultas.consultar_jugadores_por_liga, liga)


@router.get("/por-pais-del-club/{pais}")
def jugadores_por_pais_del_club(pais: str):
    return _ejecutar(consultas.consultar_jugadores_por_pais_club, pais)


@router.get("/por-antiguedad-del-club/{anio}")
def jugadores_por_antiguedad_del_club(anio: int):
    return _ejecutar(consultas.consultar_jugadores_por_antiguedad_club, anio)


@router.get("/comparar")
def comparar_jugadores(jugador_1: str = Query(..., min_length=1, max_length=100), jugador_2: str = Query(..., min_length=1, max_length=100)):
    return _ejecutar(consultas.comparar_jugadores, jugador_1, jugador_2)


# Rutas anteriores conservadas para no romper clientes existentes.
@router.get("/posicion/{posicion}")
def obtener_jugadores_por_posicion(posicion: str):
    return jugadores_por_posicion(posicion)


@router.get("/cantidad/{posicion}")
def obtener_cantidad(posicion: str):
    filas = _ejecutar(consultas.consultar_cantidad_por_posicion)
    coincidencia = next((fila for fila in filas if fila["posicion"].casefold() == posicion.casefold()), None)
    return {"posicion": posicion, "cantidad": coincidencia["cantidad_jugadores"] if coincidencia else 0}


@router.get("/numero/{numero}")
def obtener_jugador_por_numero(numero: int):
    return jugadores_por_numero(numero)
