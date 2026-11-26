from fastapi import APIRouter, HTTPException, Path, Query
from mysql.connector import Error as MySQLError

from routers import chat_tools as consultas

router = APIRouter(prefix="/jugadores", tags=["jugadores"])

RESPUESTA_JUGADORES = {
    200: {
        "description": "Registros obtenidos de jugadores y el nombre del club relacionado.",
        "content": {"application/json": {"example": [{
            "id_jugador": 7, "nombre": "Jude", "apellido": "Bellingham",
            "edad": 23, "nacionalidad": "Inglaterra", "posicion": "Mediocampista",
            "numero_camiseta": 5, "valor_mercado": 180.0, "altura": 1.86,
            "peso": 75.0, "pie_dominante": "Derecho", "imagen": None,
            "id_club": 1, "club": "Real Madrid",
        }]}}
    }
}

RESPUESTA_GOLES = {
    200: {
        "description": "Estadística basada exclusivamente en la columna jugadores.goles. Si no existe, disponible será false.",
        "content": {"application/json": {"examples": {
            "disponible": {"summary": "Columna disponible", "value": {
                "disponible": True, "cantidad": 2, "jugadores": [
                    {"id_jugador": 15, "nombre": "Lionel", "apellido": "Messi", "goles": 8, "club": "Inter Miami"},
                    {"id_jugador": 1, "nombre": "Kylian", "apellido": "Mbappé", "goles": 10, "club": "Real Madrid"},
                ]
            }},
            "no_disponible": {"summary": "La base no tiene la columna goles", "value": {
                "disponible": False,
                "mensaje": "La tabla jugadores no contiene la columna goles; no se calcularon estadísticas de goles.",
            }},
        }}}
    }
}


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


@router.get("/buscar", summary="Buscar jugadores por nombre, apellido o posición", responses=RESPUESTA_JUGADORES)
def buscar_jugador(
    nombre: str | None = Query(None, min_length=1, max_length=100, description="Coincidencia parcial en el nombre", examples=["Jude"]),
    apellido: str | None = Query(None, min_length=1, max_length=100, description="Coincidencia parcial en el apellido", examples=["Bellingham"]),
    posicion: str | None = Query(None, min_length=1, max_length=30, description="Coincidencia parcial en la posición", examples=["Defensa"]),
):
    """Busca por uno o varios campos; conserva compatibilidad con ?nombre=..."""
    return _ejecutar(consultas.buscar_jugadores_por_campos, nombre or "", apellido or "", posicion or "")


@router.get(
    "/detalle/{id_jugador}",
    summary="Consultar el registro completo de un jugador",
    responses={**RESPUESTA_JUGADORES, 404: {"description": "No existe un jugador con ese ID."}},
)
def detalle_jugador(id_jugador: int = Path(..., ge=1, description="ID del jugador en MySQL")):
    """Devuelve los campos almacenados de jugadores y el nombre de su club."""
    jugador = _ejecutar(consultas.obtener_jugador_detallado, id_jugador)
    if jugador.get("encontrado") is False:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")
    return jugador


@router.get("/defensas", summary="Listar defensas", responses=RESPUESTA_JUGADORES)
def listar_defensas():
    """Lista jugadores cuya posición registrada corresponde a defensa."""
    return _ejecutar(consultas.consultar_jugadores_por_categoria, "defensas")


@router.get("/defensas/por-club", summary="Listar defensas de un club", responses=RESPUESTA_JUGADORES)
def defensas_por_club(
    club: str = Query(..., min_length=1, max_length=100, description="Nombre o fragmento del club", examples=["Barcelona"]),
):
    return _ejecutar(consultas.consultar_categoria_por_club, "defensas", club)


@router.get("/defensas/por-seleccion", summary="Listar defensas de una selección", responses=RESPUESTA_JUGADORES)
def defensas_por_seleccion(
    seleccion: str = Query(..., min_length=1, max_length=100, description="Nacionalidad guardada en jugadores", examples=["España"]),
):
    return _ejecutar(consultas.consultar_categoria_por_seleccion, "defensas", seleccion)


@router.get("/mediocampistas", summary="Listar mediocampistas", responses=RESPUESTA_JUGADORES)
def listar_mediocampistas():
    """Incluye las etiquetas de posición mediocampista, centrocampista o medio."""
    return _ejecutar(consultas.consultar_jugadores_por_categoria, "mediocampistas")


@router.get("/mediocampistas/por-club", summary="Listar mediocampistas de un club", responses=RESPUESTA_JUGADORES)
def mediocampistas_por_club(
    club: str = Query(..., min_length=1, max_length=100, description="Nombre o fragmento del club", examples=["Barcelona"]),
):
    return _ejecutar(consultas.consultar_categoria_por_club, "mediocampistas", club)


@router.get("/mediocampistas/por-seleccion", summary="Listar mediocampistas de una selección", responses=RESPUESTA_JUGADORES)
def mediocampistas_por_seleccion(
    seleccion: str = Query(..., min_length=1, max_length=100, description="Nacionalidad guardada en jugadores", examples=["Argentina"]),
):
    return _ejecutar(consultas.consultar_categoria_por_seleccion, "mediocampistas", seleccion)


@router.get("/goles", summary="Listar goles registrados por jugador", responses=RESPUESTA_GOLES)
def goles_por_jugador(
    limite: int = Query(100, ge=1, le=100, description="Máximo de jugadores", examples=[10]),
    posicion: str | None = Query(None, min_length=1, max_length=30, description="Filtra por posición", examples=["Defensa"]),
):
    """Ordena el dato almacenado en goles. Si la columna no existe, lo indica en JSON."""
    return _ejecutar(consultas.consultar_goles_por_jugador, limite, posicion or "")


@router.get("/goles/maximo-goleador", summary="Consultar al máximo goleador", responses=RESPUESTA_GOLES)
def maximo_goleador(
    posicion: str | None = Query(None, min_length=1, max_length=30, description="Filtro opcional por posición", examples=["Mediocampista"]),
):
    """Devuelve el máximo registrado y todos los jugadores empatados."""
    return _ejecutar(consultas.consultar_maximo_goleador, posicion or "")


@router.get("/goles/promedio", summary="Calcular el promedio de goles", responses=RESPUESTA_GOLES)
def promedio_goles(
    posicion: str | None = Query(None, min_length=1, max_length=30, description="Filtro opcional por posición", examples=["Defensa"]),
):
    return _ejecutar(consultas.consultar_promedio_goles, posicion or "")


@router.get("/goles/por-club", summary="Agrupar goles por club", responses=RESPUESTA_GOLES)
def goles_por_club():
    return _ejecutar(consultas.consultar_goles_agrupados, "club")


@router.get("/goles/por-seleccion", summary="Agrupar goles por selección", responses=RESPUESTA_GOLES)
def goles_por_seleccion():
    """Agrupa por el campo nacionalidad, que representa la selección en este esquema."""
    return _ejecutar(consultas.consultar_goles_agrupados, "seleccion")


@router.get("/goles/comparar", summary="Comparar goles entre jugadores", responses=RESPUESTA_GOLES)
def comparar_goles(
    nombres: list[str] = Query(..., description="Repite el parámetro para cada jugador; admite entre 2 y 10 nombres", examples=["Lionel Messi", "Kylian Mbappe"]),
):
    return _ejecutar(consultas.comparar_goles_jugadores, nombres)


@router.get("/estadisticas/por-posicion", summary="Estadísticas generales agrupadas por posición", responses=RESPUESTA_GOLES)
def estadisticas_por_posicion():
    """Devuelve cantidad y edad promedio; incorpora goles solo si existe esa columna."""
    return _ejecutar(consultas.consultar_estadisticas_por_posicion)


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
