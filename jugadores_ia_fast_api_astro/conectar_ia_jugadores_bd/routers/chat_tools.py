"""Herramientas controladas de consulta para Gemini; nunca reciben SQL del usuario."""
from decimal import Decimal

from database import consultar_todos, consultar_uno

LIMITE_RESULTADOS = 100
SELECT_JUGADORES = """SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
    j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado,
    j.altura, j.peso, j.pie_dominante, j.imagen, j.id_club,
    c.nombre AS club FROM jugadores j JOIN clubes c ON c.id_club = j.id_club"""
SELECT_CLUBES = """SELECT id_club, nombre, pais, liga, estadio, anio_fundacion
    FROM clubes"""


def _normalizar(valor):
    if isinstance(valor, list):
        return [_normalizar(item) for item in valor]
    if isinstance(valor, dict):
        return {clave: _normalizar(item) for clave, item in valor.items()}
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def _texto(valor, etiqueta):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > 100:
        raise ValueError(f"{etiqueta} debe ser texto de 1 a 100 caracteres.")
    return valor.strip()


def _entero(valor, etiqueta, minimo=0, maximo=10000):
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ValueError(f"{etiqueta} debe ser un entero entre {minimo} y {maximo}.")
    return valor


def _jugadores(sql=SELECT_JUGADORES, parametros=()):
    return _normalizar(consultar_todos(sql + " LIMIT %s", tuple(parametros) + (LIMITE_RESULTADOS,)))


def _agregado(sql, parametros=()):
    if " LIMIT " not in sql.upper():
        sql += " LIMIT %s"
        parametros = tuple(parametros) + (LIMITE_RESULTADOS,)
    return _normalizar(consultar_todos(sql, parametros))


def consultar_jugadores() -> list:
    """Devuelve hasta 100 jugadores con sus datos principales y club."""
    return _jugadores(SELECT_JUGADORES + " ORDER BY j.apellido, j.nombre")


def buscar_jugador(nombre: str) -> list:
    """Busca jugadores por coincidencia parcial de nombre, apellido o nombre completo."""
    nombre = _texto(nombre, "nombre")
    patron = f"%{nombre}%"
    return _jugadores(SELECT_JUGADORES + " WHERE j.nombre LIKE %s OR j.apellido LIKE %s OR CONCAT(j.nombre, ' ', j.apellido) LIKE %s ORDER BY j.apellido, j.nombre", (patron, patron, patron))


def obtener_imagen_jugador(nombre: str) -> dict:
    """Devuelve imagen, nombre y club de coincidencias; imagen puede ser NULL."""
    filas = buscar_jugador(nombre)
    if not filas:
        return {"encontrado": False, "jugadores": []}
    return {"encontrado": True, "jugadores": [
        {"nombre": f"{fila['nombre']} {fila['apellido']}", "club": fila["club"], "imagen": fila["imagen"]}
        for fila in filas
    ]}


def consultar_jugadores_por_edad(edad_minima: int, edad_maxima: int) -> list:
    """Filtra jugadores por edad inclusiva, con un máximo de 100 resultados."""
    edad_minima = _entero(edad_minima, "edad_minima", 0, 120)
    edad_maxima = _entero(edad_maxima, "edad_maxima", 0, 120)
    if edad_minima > edad_maxima:
        raise ValueError("edad_minima no puede ser mayor que edad_maxima.")
    return _jugadores(SELECT_JUGADORES + " WHERE j.edad BETWEEN %s AND %s ORDER BY j.edad, j.apellido, j.nombre", (edad_minima, edad_maxima))


def consultar_jugadores_por_numero(numero: int) -> list:
    """Busca jugadores por número de camiseta."""
    numero = _entero(numero, "numero", 0, 999)
    return _jugadores(SELECT_JUGADORES + " WHERE j.numero_camiseta = %s ORDER BY j.apellido, j.nombre", (numero,))


def consultar_jugadores_ordenados(criterio: str) -> list:
    """Ordena jugadores por nombre, apellido, edad o valor de mercado."""
    permitidos = {"nombre": "j.nombre", "apellido": "j.apellido", "edad": "j.edad", "valor de mercado": "j.valor_mercado", "valor_mercado": "j.valor_mercado"}
    clave = _texto(criterio, "criterio").casefold()
    if clave not in permitidos:
        return {"error": "Criterio no permitido. Usa nombre, apellido, edad o valor de mercado."}
    return _jugadores(SELECT_JUGADORES + f" ORDER BY {permitidos[clave]} ASC, j.apellido, j.nombre")


def consultar_por_nacionalidad(nacionalidad: str) -> list:
    """Filtra jugadores por nacionalidad (coincidencia parcial)."""
    nacionalidad = _texto(nacionalidad, "nacionalidad")
    return _jugadores(SELECT_JUGADORES + " WHERE j.nacionalidad LIKE %s ORDER BY j.apellido, j.nombre", (f"%{nacionalidad}%",))


def consultar_nacionalidades() -> list:
    """Lista nacionalidades disponibles y su cantidad de jugadores."""
    return _agregado("""SELECT nacionalidad, COUNT(*) AS cantidad_jugadores
        FROM jugadores WHERE nacionalidad IS NOT NULL AND nacionalidad <> ''
        GROUP BY nacionalidad ORDER BY cantidad_jugadores DESC, nacionalidad""")


def consultar_por_posicion(posicion: str) -> list:
    """Filtra jugadores por posición, aceptando coincidencia parcial."""
    posicion = _texto(posicion, "posicion")
    return _jugadores(SELECT_JUGADORES + " WHERE j.posicion LIKE %s ORDER BY j.apellido, j.nombre", (f"%{posicion}%",))


def consultar_cantidad_por_posicion() -> list:
    """Cuenta los jugadores por posición."""
    return _agregado("""SELECT posicion, COUNT(*) AS cantidad_jugadores
        FROM jugadores WHERE posicion IS NOT NULL AND posicion <> ''
        GROUP BY posicion ORDER BY cantidad_jugadores DESC, posicion""")


def consultar_promedio_edad_por_posicion() -> list:
    """Calcula la edad promedio agrupada por posición."""
    return _agregado("""SELECT posicion, COUNT(*) AS cantidad_jugadores,
        AVG(edad) AS edad_promedio FROM jugadores
        WHERE posicion IS NOT NULL AND edad IS NOT NULL
        GROUP BY posicion ORDER BY posicion""")


def _extremo_jugador(campo: str, orden: str, alias: str) -> dict:
    permitidos = {"altura", "peso", "valor_mercado"}
    if campo not in permitidos or orden not in {"ASC", "DESC"}:
        raise ValueError("Criterio interno no permitido.")
    fila = consultar_uno(SELECT_JUGADORES + f" WHERE j.{campo} IS NOT NULL ORDER BY j.{campo} {orden}, j.id_jugador LIMIT 1")
    return _normalizar({alias: fila})


def consultar_jugador_mas_alto() -> dict:
    """Identifica al jugador con mayor altura registrada."""
    return _extremo_jugador("altura", "DESC", "mas_alto")


def consultar_jugador_mas_bajo() -> dict:
    """Identifica al jugador con menor altura registrada."""
    return _extremo_jugador("altura", "ASC", "mas_bajo")


def consultar_jugador_mas_pesado() -> dict:
    """Identifica al jugador con mayor peso registrado."""
    return _extremo_jugador("peso", "DESC", "mas_pesado")


def consultar_promedios_fisicos() -> dict:
    """Calcula altura y peso promedio desde MySQL."""
    return _normalizar(consultar_uno("SELECT AVG(altura) AS altura_promedio, AVG(peso) AS peso_promedio FROM jugadores"))


def consultar_por_pie_dominante(pie: str) -> list:
    """Filtra por pie dominante derecho o izquierdo."""
    pie = _texto(pie, "pie").casefold()
    valores = {"derecho": ("derecho", "right", "right foot"), "diestro": ("derecho", "right", "right foot"), "right": ("derecho", "right", "right foot"), "izquierdo": ("izquierdo", "left", "left foot"), "zurdo": ("izquierdo", "left", "left foot"), "left": ("izquierdo", "left", "left foot")}
    if pie not in valores:
        return {"error": "Pie no permitido. Indica derecho/diestro o izquierdo/zurdo."}
    opciones = valores[pie]
    marcas = ", ".join(["%s"] * len(opciones))
    return _jugadores(SELECT_JUGADORES + f" WHERE LOWER(j.pie_dominante) IN ({marcas}) ORDER BY j.apellido, j.nombre", opciones)


def consultar_jugador_mas_valioso() -> dict:
    """Identifica al jugador con mayor valor de mercado registrado."""
    return _extremo_jugador("valor_mercado", "DESC", "mas_valioso")


def consultar_jugador_menos_valioso() -> dict:
    """Identifica al jugador con menor valor de mercado registrado."""
    return _extremo_jugador("valor_mercado", "ASC", "menos_valioso")


def consultar_valor_total_mercado() -> dict:
    """Suma el valor de mercado de todos los jugadores."""
    return _normalizar(consultar_uno("SELECT SUM(valor_mercado) AS valor_total_mercado FROM jugadores"))


def consultar_promedio_valor_mercado() -> dict:
    """Calcula el valor promedio de mercado de los jugadores."""
    return _normalizar(consultar_uno("SELECT AVG(valor_mercado) AS valor_promedio_mercado FROM jugadores"))


def consultar_jugadores_por_valor(valor_minimo: float, valor_maximo: float) -> list:
    """Filtra jugadores por rango inclusivo de valor de mercado."""
    minimo, maximo = _numero_mercado(valor_minimo, "valor_minimo"), _numero_mercado(valor_maximo, "valor_maximo")
    if minimo > maximo:
        raise ValueError("valor_minimo no puede ser mayor que valor_maximo.")
    return _jugadores(SELECT_JUGADORES + " WHERE j.valor_mercado BETWEEN %s AND %s ORDER BY j.valor_mercado DESC, j.apellido, j.nombre", (minimo, maximo))


def _numero_mercado(valor, etiqueta):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not 0 <= valor <= 1000000:
        raise ValueError(f"{etiqueta} debe ser un número entre 0 y 1,000,000 (millones de euros).")
    return valor


def consultar_valor_mercado_por_nacionalidad() -> list:
    """Suma el valor de mercado por nacionalidad."""
    return _normalizar(_agregado("""SELECT nacionalidad, COUNT(*) AS cantidad_jugadores,
        SUM(valor_mercado) AS valor_mercado_total FROM jugadores
        WHERE nacionalidad IS NOT NULL GROUP BY nacionalidad
        ORDER BY valor_mercado_total DESC, nacionalidad"""))


def consultar_clubes() -> list:
    """Devuelve los clubes registrados."""
    return _agregado(SELECT_CLUBES + " ORDER BY nombre LIMIT %s", (LIMITE_RESULTADOS,))


def buscar_club(nombre: str) -> list:
    """Busca clubes por nombre, con coincidencia parcial."""
    nombre = _texto(nombre, "nombre")
    return _agregado(SELECT_CLUBES + " WHERE nombre LIKE %s ORDER BY nombre LIMIT %s", (f"%{nombre}%", LIMITE_RESULTADOS))


def consultar_clubes_por_pais(pais: str) -> list:
    """Filtra clubes por país."""
    pais = _texto(pais, "pais")
    return _agregado(SELECT_CLUBES + " WHERE pais LIKE %s ORDER BY nombre LIMIT %s", (f"%{pais}%", LIMITE_RESULTADOS))


def consultar_clubes_por_liga(liga: str) -> list:
    """Filtra clubes por liga."""
    liga = _texto(liga, "liga")
    return _agregado(SELECT_CLUBES + " WHERE liga LIKE %s ORDER BY nombre LIMIT %s", (f"%{liga}%", LIMITE_RESULTADOS))


def consultar_jugadores_por_club(club: str, posicion: str = "") -> list:
    """Busca jugadores de un club, opcionalmente filtrados por posición."""
    club = _texto(club, "club")
    sql = SELECT_JUGADORES + " WHERE c.nombre LIKE %s"
    parametros = (f"%{club}%",)
    if posicion:
        posicion = _texto(posicion, "posicion")
        sql += " AND j.posicion LIKE %s"
        parametros += (f"%{posicion}%",)
    return _jugadores(sql + " ORDER BY j.apellido, j.nombre", parametros)


def consultar_cantidad_jugadores_por_club() -> list:
    """Cuenta jugadores por club, incluidos clubes sin jugadores."""
    return _agregado("""SELECT c.id_club, c.nombre AS club, COUNT(j.id_jugador) AS cantidad_jugadores
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        GROUP BY c.id_club, c.nombre ORDER BY cantidad_jugadores DESC, c.nombre""")


def consultar_jugadores_por_liga(liga: str) -> list:
    """Lista jugadores vinculados a clubes de una liga."""
    liga = _texto(liga, "liga")
    return _jugadores(SELECT_JUGADORES + " WHERE c.liga LIKE %s ORDER BY c.nombre, j.apellido, j.nombre", (f"%{liga}%",))


def consultar_valor_mercado_por_liga() -> list:
    """Suma el valor de mercado de las plantillas por liga."""
    return _normalizar(_agregado("""SELECT c.liga, COUNT(j.id_jugador) AS cantidad_jugadores,
        SUM(j.valor_mercado) AS valor_mercado_total
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        GROUP BY c.liga ORDER BY valor_mercado_total DESC, c.liga"""))


def consultar_estadisticas_por_club() -> list:
    """Agrupa cantidad de jugadores, edad promedio y valor acumulado por club."""
    return _normalizar(_agregado("""SELECT c.id_club, c.nombre AS club,
        COUNT(j.id_jugador) AS cantidad_jugadores, AVG(j.edad) AS edad_promedio,
        SUM(j.valor_mercado) AS valor_mercado_total
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        GROUP BY c.id_club, c.nombre ORDER BY cantidad_jugadores DESC, c.nombre"""))


def consultar_estadisticas_jugadores() -> dict:
    """Resume total y promedios globales, además de los extremos registrados."""
    resumen = consultar_uno("""SELECT COUNT(*) AS total_jugadores,
        AVG(edad) AS edad_promedio, AVG(altura) AS altura_promedio,
        AVG(valor_mercado) AS valor_mercado_promedio FROM jugadores""")
    extremos = {}
    for nombre, campo, orden in (
        ("mas_joven", "edad", "ASC"), ("mayor_edad", "edad", "DESC"),
        ("mas_alto", "altura", "DESC"), ("mas_bajo", "altura", "ASC"),
        ("mas_valioso", "valor_mercado", "DESC"),
        ("menos_valioso", "valor_mercado", "ASC"),
    ):
        extremos[nombre] = consultar_uno(
            SELECT_JUGADORES + f" WHERE j.{campo} IS NOT NULL ORDER BY j.{campo} {orden}, j.id_jugador LIMIT 1"
        )
    return _normalizar({**(resumen or {}), **extremos})


def obtener_informacion_club(club: str) -> dict:
    """Devuelve información de un club exacto y su cantidad de jugadores."""
    club = _texto(club, "club")
    fila = consultar_uno("""SELECT c.id_club, c.nombre, c.pais, c.liga, c.estadio,
        c.anio_fundacion, COUNT(j.id_jugador) AS jugadores_registrados
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        WHERE LOWER(c.nombre) = LOWER(%s)
        GROUP BY c.id_club, c.nombre, c.pais, c.liga, c.estadio, c.anio_fundacion""", (club,))
    return _normalizar(fila or {"encontrado": False, "club": club})


def comparar_jugadores(jugador_1: str, jugador_2: str) -> list:
    """Compara dos jugadores por nombre y devuelve sus datos disponibles."""
    jugador_1, jugador_2 = _texto(jugador_1, "jugador_1"), _texto(jugador_2, "jugador_2")
    return _jugadores(SELECT_JUGADORES + " WHERE CONCAT(j.nombre, ' ', j.apellido) LIKE %s OR CONCAT(j.nombre, ' ', j.apellido) LIKE %s ORDER BY j.apellido, j.nombre", (f"%{jugador_1}%", f"%{jugador_2}%"))


def consultar_jugadores_por_pais_club(pais: str) -> list:
    """Lista jugadores de clubes ubicados en el país indicado."""
    pais = _texto(pais, "pais")
    return _jugadores(SELECT_JUGADORES + " WHERE c.pais LIKE %s ORDER BY c.nombre, j.apellido, j.nombre", (f"%{pais}%",))


def comparar_clubes(club_1: str, club_2: str) -> list:
    """Compara cantidad, edad promedio y valor de mercado total de dos clubes."""
    club_1, club_2 = _texto(club_1, "club_1"), _texto(club_2, "club_2")
    return _normalizar(_agregado("""SELECT c.nombre AS club,
        COUNT(j.id_jugador) AS cantidad_jugadores, AVG(j.edad) AS edad_promedio,
        SUM(j.valor_mercado) AS valor_mercado_total
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        WHERE LOWER(c.nombre) IN (LOWER(%s), LOWER(%s))
        GROUP BY c.id_club, c.nombre ORDER BY c.nombre""", (club_1, club_2)))


def consultar_jugadores_por_antiguedad_club(anio: int) -> list:
    """Lista jugadores de clubes fundados antes del año indicado."""
    anio = _entero(anio, "anio", 1800, 2100)
    return _jugadores(SELECT_JUGADORES + " WHERE c.anio_fundacion < %s ORDER BY c.anio_fundacion, c.nombre, j.apellido, j.nombre", (anio,))


HERRAMIENTAS_GEMINI = [
    consultar_jugadores, buscar_jugador, consultar_jugadores_por_edad,
    consultar_jugadores_por_numero, consultar_jugadores_ordenados,
    consultar_por_nacionalidad, consultar_nacionalidades, consultar_por_posicion,
    consultar_cantidad_por_posicion, consultar_promedio_edad_por_posicion,
    consultar_jugador_mas_alto, consultar_jugador_mas_bajo,
    consultar_jugador_mas_pesado, consultar_promedios_fisicos,
    consultar_por_pie_dominante, consultar_jugador_mas_valioso,
    consultar_jugador_menos_valioso, consultar_valor_total_mercado,
    consultar_promedio_valor_mercado, consultar_jugadores_por_valor,
    consultar_valor_mercado_por_nacionalidad, consultar_clubes, buscar_club,
    consultar_clubes_por_pais, consultar_clubes_por_liga,
    consultar_jugadores_por_club, consultar_cantidad_jugadores_por_club,
    consultar_jugadores_por_liga, consultar_valor_mercado_por_liga,
    consultar_estadisticas_por_club, consultar_jugadores_por_pais_club,
    comparar_clubes, consultar_jugadores_por_antiguedad_club,
    obtener_imagen_jugador, consultar_estadisticas_jugadores,
    obtener_informacion_club, comparar_jugadores,
]
