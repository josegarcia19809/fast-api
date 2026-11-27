from fastapi import APIRouter, HTTPException, Query
from mysql.connector import Error as MySQLError
from pydantic import BaseModel, Field, validator

from database import consultar_todos, consultar_uno, ejecutar_modificacion
from routers import chat_tools as consultas

router = APIRouter(prefix="/clubes", tags=["clubes"])


class ClubEntrada(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    pais: str = Field(..., min_length=1, max_length=60)
    liga: str = Field(..., min_length=1, max_length=80)
    estadio: str | None = Field(None, max_length=100)
    anio_fundacion: int | None = Field(None, ge=1800, le=2100)

    @validator("nombre", "pais", "liga")
    def texto_requerido(cls, valor):
        valor = valor.strip()
        if not valor:
            raise ValueError("Este campo no puede quedar vacío.")
        return valor

    class Config:
        extra = "forbid"


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


@router.get("/administracion")
def listar_clubes_administracion():
    try:
        return consultar_todos("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes ORDER BY nombre")
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al consultar los clubes.") from error


@router.post("/", status_code=201)
def crear_club(club: ClubEntrada):
    try:
        resultado = ejecutar_modificacion(
            "INSERT INTO clubes (nombre, pais, liga, estadio, anio_fundacion) VALUES (%s, %s, %s, %s, %s)",
            (club.nombre.strip(), club.pais.strip(), club.liga.strip(), club.estadio.strip() if club.estadio else None, club.anio_fundacion),
        )
        return obtener_club(resultado["id"])
    except MySQLError as error:
        if getattr(error, "errno", None) == 1062:
            raise HTTPException(status_code=409, detail="Ya existe un club con ese nombre.") from error
        raise HTTPException(status_code=500, detail="No fue posible guardar el club.") from error


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
    try:
        club = consultar_uno("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes WHERE id_club = %s", (id_club,))
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="Error al acceder a MySQL.") from error
    if club is None:
        raise HTTPException(status_code=404, detail="Club no encontrado")
    return club


@router.put("/{id_club}")
def actualizar_club(id_club: int, club: ClubEntrada):
    try:
        existente = consultar_uno("SELECT id_club FROM clubes WHERE id_club = %s", (id_club,))
        if existente is None:
            raise HTTPException(status_code=404, detail="Club no encontrado")
        ejecutar_modificacion(
            "UPDATE clubes SET nombre = %s, pais = %s, liga = %s, estadio = %s, anio_fundacion = %s WHERE id_club = %s",
            (club.nombre.strip(), club.pais.strip(), club.liga.strip(), club.estadio.strip() if club.estadio else None, club.anio_fundacion, id_club),
        )
        return obtener_club(id_club)
    except HTTPException:
        raise
    except MySQLError as error:
        if getattr(error, "errno", None) == 1062:
            raise HTTPException(status_code=409, detail="Ya existe otro club con ese nombre.") from error
        raise HTTPException(status_code=500, detail="No fue posible actualizar el club.") from error


@router.delete("/{id_club}", status_code=204)
def eliminar_club(id_club: int):
    try:
        resultado = ejecutar_modificacion("DELETE FROM clubes WHERE id_club = %s", (id_club,))
        if resultado["filas"] == 0:
            raise HTTPException(status_code=404, detail="Club no encontrado")
        return None
    except HTTPException:
        raise
    except MySQLError as error:
        if getattr(error, "errno", None) == 1451:
            raise HTTPException(status_code=409, detail="No se puede eliminar el club porque tiene jugadores asociados.") from error
        raise HTTPException(status_code=500, detail="No fue posible eliminar el club.") from error
