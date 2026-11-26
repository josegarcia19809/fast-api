from fastapi import APIRouter, HTTPException, Query
from mysql.connector import Error as MySQLError

from routers import chat_tools as consultas

router = APIRouter(prefix="/clubes", tags=["clubes"])


def _ejecutar(funcion, *args):
    try:
        return funcion(*args)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al acceder a MySQL.") from error


@router.get("/")
def obtener_clubes():
    return _ejecutar(consultas.consultar_clubes)


@router.get("/buscar")
def buscar_club(nombre: str = Query(..., min_length=1, max_length=100)):
    return _ejecutar(consultas.buscar_club, nombre)


@router.get("/por-pais/{pais}")
def clubes_por_pais(pais: str):
    return _ejecutar(consultas.consultar_clubes_por_pais, pais)


@router.get("/por-liga/{liga}")
def clubes_por_liga(liga: str):
    return _ejecutar(consultas.consultar_clubes_por_liga, liga)


@router.get("/estadisticas")
def estadisticas_por_club():
    return _ejecutar(consultas.consultar_estadisticas_por_club)


@router.get("/cantidad-de-jugadores")
def cantidad_jugadores_por_club():
    return _ejecutar(consultas.consultar_cantidad_jugadores_por_club)


@router.get("/valor-mercado/por-liga")
def valor_mercado_por_liga():
    return _ejecutar(consultas.consultar_valor_mercado_por_liga)


@router.get("/valor-mercado/ranking")
def ranking_valor_mercado():
    filas = _ejecutar(consultas.consultar_estadisticas_por_club)
    return sorted(filas, key=lambda fila: fila.get("valor_mercado_total") or 0, reverse=True)


@router.get("/comparar")
def comparar_clubes(club_1: str = Query(..., min_length=1, max_length=100), club_2: str = Query(..., min_length=1, max_length=100)):
    return _ejecutar(consultas.comparar_clubes, club_1, club_2)


@router.get("/nombre/{nombre}")
def informacion_club(nombre: str):
    return _ejecutar(consultas.obtener_informacion_club, nombre)


@router.get("/{id_club}/jugadores")
def obtener_jugadores_del_club(id_club: int, posicion: str | None = None):
    from database import consultar_uno

    try:
        club = consultar_uno("SELECT id_club, nombre FROM clubes WHERE id_club = %s", (id_club,))
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al acceder a MySQL.") from error
    if club is None:
        raise HTTPException(status_code=404, detail="Club no encontrado")
    return _ejecutar(consultas.consultar_jugadores_por_club, club["nombre"], posicion or "")


@router.get("/{id_club}")
def obtener_club(id_club: int):
    # Conserva la ruta existente basada en ID; el chat busca por nombre.
    from database import consultar_uno

    try:
        club = consultar_uno("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes WHERE id_club = %s", (id_club,))
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al acceder a MySQL.") from error
    if club is None:
        raise HTTPException(status_code=404, detail="Club no encontrado")
    return club
