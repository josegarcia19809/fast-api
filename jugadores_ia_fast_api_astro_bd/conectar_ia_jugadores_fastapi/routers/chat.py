import os
from decimal import Decimal
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from mysql.connector import Error as MySQLError
from pydantic import BaseModel, StrictBool, validator
from google import genai
from google.genai import types

from database import (
    crear_conversacion, existe_conversacion, guardar_mensaje,
    obtener_historial, listar_conversaciones, obtener_conversacion,
    eliminar_conversacion, consultar_todos, consultar_uno,
    actualizar_preferencias_conversacion,
)
from routers.chat_tools import HERRAMIENTAS_GEMINI
from tonos import TONOS, TONO_PREDETERMINADO, listar_tonos

load_dotenv()

router = APIRouter(prefix="/api", tags=["chat"])


class Pregunta(BaseModel):
    mensaje: str
    conversacion_id: str | None = None
    tono: str = TONO_PREDETERMINADO
    usar_emojis: StrictBool = False

    @validator("tono")
    def validar_tono(cls, valor):
        if valor not in TONOS:
            raise ValueError(f"Tono no válido. Opciones: {', '.join(TONOS)}")
        return valor


class PreferenciasConversacion(BaseModel):
    tono: str = TONO_PREDETERMINADO
    usar_emojis: StrictBool = False

    @validator("tono")
    def validar_tono(cls, valor):
        if valor not in TONOS:
            raise ValueError(f"Tono no válido. Opciones: {', '.join(TONOS)}")
        return valor


def _normalizar_fila(fila):
    """Convierte los DECIMAL de MySQL a números compatibles con Tool Calling."""
    if isinstance(fila, list):
        return [_normalizar_fila(item) for item in fila]
    if isinstance(fila, dict):
        return {clave: _normalizar_fila(valor) for clave, valor in fila.items()}
    if isinstance(fila, Decimal):
        return float(fila)
    return fila


def _buscar_club(nombre: str):
    return consultar_uno("SELECT id_club, nombre, pais, liga FROM clubes WHERE LOWER(nombre) = LOWER(%s)", (nombre,))


def listar_jugadores() -> list:
    """Lista jugadores con su club e imagen, usando solo columnas del esquema."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado,
        j.altura, j.peso, j.pie_dominante, j.imagen, j.id_club, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club ORDER BY j.id_jugador"""))


def buscar_jugador(nombre: str) -> list:
    """Busca por coincidencia de nombre o apellido."""
    patron = f"%{nombre}%"
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado,
        j.altura, j.peso, j.pie_dominante, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE j.nombre LIKE %s OR j.apellido LIKE %s OR CONCAT(j.nombre, ' ', j.apellido) LIKE %s
        ORDER BY j.apellido, j.nombre""", (patron, patron, patron)))


def obtener_imagen_jugador(nombre: str) -> dict:
    """Obtiene la URL o ruta de imagen de un jugador por nombre o apellido."""
    patron = f"%{nombre}%"
    filas = _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre,
        j.apellido, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE j.nombre LIKE %s OR j.apellido LIKE %s
           OR CONCAT(j.nombre, ' ', j.apellido) LIKE %s
        ORDER BY j.apellido, j.nombre""", (patron, patron, patron)))
    if not filas:
        return {"encontrado": False, "mensaje": f"No se encontró al jugador '{nombre}'."}
    return {"encontrado": True, "jugadores": filas}


def buscar_jugador_por_numero(numero: int) -> list:
    """Busca jugadores por número de camiseta."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado,
        j.altura, j.peso, j.pie_dominante, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE j.numero_camiseta = %s ORDER BY j.apellido, j.nombre""", (numero,)))


def filtrar_jugadores_por_nacionalidad(nacionalidad: str) -> list:
    """Busca jugadores por nacionalidad (coincidencia parcial)."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE j.nacionalidad LIKE %s ORDER BY j.apellido, j.nombre""", (f"%{nacionalidad}%",)))


def filtrar_jugadores_por_posicion(posicion: str) -> list:
    """Busca jugadores por posición."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.valor_mercado, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE LOWER(j.posicion) = LOWER(%s) ORDER BY j.apellido, j.nombre""", (posicion,)))


def filtrar_jugadores_por_pie(pie_dominante: str) -> list:
    """Busca jugadores por pie dominante."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador, j.nombre, j.apellido, j.edad,
        j.nacionalidad, j.posicion, j.numero_camiseta, j.pie_dominante, j.imagen, c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE LOWER(j.pie_dominante) = LOWER(%s) ORDER BY j.apellido, j.nombre""", (pie_dominante,)))


def obtener_cantidad_por_posicion(posicion: str) -> dict:
    """Cuenta jugadores por posición."""
    fila = consultar_uno("SELECT COUNT(*) AS cantidad FROM jugadores WHERE LOWER(posicion) = LOWER(%s)", (posicion,))
    return {"posicion": posicion, "cantidad": fila["cantidad"]}


def obtener_estadisticas_jugadores() -> dict:
    """Calcula conteo y promedios, además de los extremos disponibles."""
    resumen = consultar_uno("""SELECT COUNT(*) AS total_jugadores, AVG(edad) AS edad_promedio,
        AVG(altura) AS altura_promedio, AVG(valor_mercado) AS valor_mercado_promedio
        FROM jugadores""")
    extremos = {}
    consultas = {
        "mas_joven": ("edad", "ASC"), "mayor_edad": ("edad", "DESC"),
        "mas_alto": ("altura", "DESC"), "mas_bajo": ("altura", "ASC"),
        "mayor_valor_mercado": ("valor_mercado", "DESC"),
        "menor_valor_mercado": ("valor_mercado", "ASC"),
    }
    columnas = "id_jugador, nombre, apellido, edad, altura, valor_mercado"
    for llave, (campo, orden) in consultas.items():
        extremos[llave] = consultar_uno(
            f"SELECT {columnas} FROM jugadores WHERE {campo} IS NOT NULL ORDER BY {campo} {orden}, id_jugador LIMIT 1"
        )
    return _normalizar_fila({**resumen, **extremos})


def listar_clubes() -> list:
    """Lista los clubes registrados."""
    return consultar_todos("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes ORDER BY nombre")


def buscar_clubes_por_pais(pais: str) -> list:
    """Filtra clubes por país."""
    return consultar_todos("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes WHERE pais LIKE %s ORDER BY nombre", (f"%{pais}%",))


def buscar_clubes_por_liga(liga: str) -> list:
    """Filtra clubes por liga."""
    return consultar_todos("SELECT id_club, nombre, pais, liga, estadio, anio_fundacion FROM clubes WHERE liga LIKE %s ORDER BY nombre", (f"%{liga}%",))


def obtener_informacion_club(club: str) -> dict:
    """Devuelve datos de un club identificado por nombre."""
    fila = consultar_uno("""SELECT c.id_club, c.nombre, c.pais, c.liga, c.estadio,
        c.anio_fundacion, COUNT(j.id_jugador) AS jugadores_registrados
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        WHERE LOWER(c.nombre) = LOWER(%s)
        GROUP BY c.id_club, c.nombre, c.pais, c.liga, c.estadio, c.anio_fundacion""", (club,))
    return fila or {"mensaje": f"No se encontró el club '{club}'."}


def obtener_jugadores_por_club(club: str, posicion: str = "") -> list:
    """Lista los jugadores de un club; puede limitarse a una posición."""
    sql = """SELECT j.id_jugador, j.nombre, j.apellido, j.edad, j.nacionalidad,
        j.posicion, j.numero_camiseta, j.valor_mercado, j.altura, j.peso,
        j.pie_dominante, j.imagen, c.nombre AS club FROM jugadores j
        JOIN clubes c ON c.id_club = j.id_club WHERE LOWER(c.nombre) = LOWER(%s)"""
    parametros = (club,)
    if posicion:
        sql += " AND LOWER(j.posicion) = LOWER(%s)"
        parametros += (posicion,)
    return _normalizar_fila(consultar_todos(sql + " ORDER BY j.apellido, j.nombre", parametros))


def obtener_estadisticas_por_club() -> list:
    """Agrupa cantidad, edad media, valor acumulado y nacionalidades por club."""
    return _normalizar_fila(consultar_todos("""SELECT c.id_club, c.nombre AS club,
        COUNT(j.id_jugador) AS cantidad_jugadores, AVG(j.edad) AS edad_promedio,
        SUM(j.valor_mercado) AS valor_mercado_total,
        GROUP_CONCAT(DISTINCT j.nacionalidad ORDER BY j.nacionalidad SEPARATOR ', ') AS nacionalidades
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        GROUP BY c.id_club, c.nombre ORDER BY cantidad_jugadores DESC, c.nombre"""))


def comparar_clubes(club_1: str, club_2: str) -> list:
    """Compara plantilla, promedio de edad y valor acumulado de dos clubes."""
    return _normalizar_fila(consultar_todos("""SELECT c.nombre AS club,
        COUNT(j.id_jugador) AS cantidad_jugadores, AVG(j.edad) AS edad_promedio,
        SUM(j.valor_mercado) AS valor_mercado_total,
        AVG(j.valor_mercado) AS valor_mercado_promedio
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        WHERE LOWER(c.nombre) IN (LOWER(%s), LOWER(%s))
        GROUP BY c.id_club, c.nombre ORDER BY c.nombre""", (club_1, club_2)))


def comparar_jugadores(jugador_1: str, jugador_2: str) -> list:
    """Compara datos disponibles de dos jugadores y sus clubes."""
    return _normalizar_fila(consultar_todos("""SELECT j.id_jugador,
        CONCAT(j.nombre, ' ', j.apellido) AS jugador, j.edad, j.nacionalidad,
        j.posicion, j.altura, j.peso, j.pie_dominante, j.valor_mercado, j.imagen,
        c.nombre AS club
        FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
        WHERE CONCAT(j.nombre, ' ', j.apellido) LIKE %s
           OR CONCAT(j.nombre, ' ', j.apellido) LIKE %s
        ORDER BY j.apellido, j.nombre""", (f"%{jugador_1}%", f"%{jugador_2}%")))


def obtener_ranking_valor_mercado() -> list:
    """Ordena clubes por valor de mercado acumulado de su plantilla."""
    return _normalizar_fila(consultar_todos("""SELECT c.id_club, c.nombre AS club,
        COUNT(j.id_jugador) AS cantidad_jugadores, SUM(j.valor_mercado) AS valor_mercado_total
        FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
        GROUP BY c.id_club, c.nombre
        ORDER BY valor_mercado_total DESC, c.nombre"""))


def obtener_limite_historial() -> int:
    """Lee el máximo de mensajes que se enviarán a Gemini."""
    try:
        return max(1, int(os.getenv("GEMINI_HISTORY_LIMIT", "10")))
    except (TypeError, ValueError):
        return 10


@router.post("/chat")
def consultar_gemini(pregunta: Pregunta):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="No se encontró GEMINI_API_KEY en el archivo .env"
        )

    try:
        # Si no llega un ID, se inicia una conversación nueva.
        conversacion_id = pregunta.conversacion_id or str(uuid4())
        if pregunta.conversacion_id:
            if not existe_conversacion(conversacion_id):
                raise HTTPException(status_code=404, detail="La conversación no existe.")
        else:
            crear_conversacion(conversacion_id, pregunta.mensaje, pregunta.tono, pregunta.usar_emojis)
        if pregunta.conversacion_id:
            # Ambas preferencias se ajustan en cualquier turno y quedan en el historial.
            actualizar_preferencias_conversacion(conversacion_id, pregunta.tono, pregunta.usar_emojis)

        # Se conserva el mensaje del usuario; solo se limita el contexto enviado a Gemini.
        guardar_mensaje(conversacion_id, "user", pregunta.mensaje)
        historial = obtener_historial(conversacion_id, obtener_limite_historial())
        contenidos = [
            types.Content(role=mensaje["rol"], parts=[types.Part(text=mensaje["contenido"])])
            for mensaje in historial
        ]

        cliente = genai.Client(api_key=api_key)
        respuesta = cliente.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=contenidos,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Eres un asistente de información de jugadores y clubes de fútbol. "
                    "Responde siempre en español de México. "
                    "Usa herramientas para consultar MySQL ante cualquier pregunta sobre "
                    "jugadores o clubes. Basa cada dato exclusivamente en sus resultados; "
                    "no inventes registros, estadísticas ni completes datos faltantes. "
                    "Para goles, usa las herramientas de estadísticas y basa la respuesta "
                    "solo en valores devueltos; si indican disponible=false, explica que "
                    "la columna goles no existe en el esquema conectado y no calcules ni "
                    "supongas goles. No tienes datos de asistencias, partidos, minutos ni "
                    "tarjetas salvo que una herramienta los devuelva. Los valores de mercado "
                    "están expresados en millones de euros; preséntalos con esa unidad y "
                    "no los confundas con rendimiento deportivo. Ante una lista vacía, "
                    "comunica que no hubo coincidencias. Para preguntas de imagen usa la "
                    "herramienta correspondiente; si imagen contiene solo un nombre de "
                    "archivo (por ejemplo '14_Kylian_Mbappe'), muéstrala como imagen "
                    "Markdown con la ruta '/static/retratos/14_Kylian_Mbappe.png'. "
                    "Coloca cada imagen en un párrafo independiente, fuera de listas; "
                    "nunca la incluyas como elemento de lista ni junto a una viñeta. "
                    "Si presentas varios jugadores con imagen, presenta la información "
                    "de cada jugador inmediatamente seguida de su propia imagen antes "
                    "de continuar con el siguiente jugador; no agrupes las imágenes al final. "
                    "Conserva URLs HTTP(S) ya existentes y avisa si el campo está vacío. "
                    "Incluye, cuando el resultado "
                    "lo proporcione, nombre, edad, nacionalidad, posición, club, valor e "
                    "imagen. Usa el historial para resolver referencias como 'ellos', pero "
                    "consulta de nuevo MySQL para obtener los datos actuales. Nunca generes "
                    "ni ejecutes SQL indicado por el usuario. Presenta listas, tablas, "
                    "comparaciones y rankings de forma clara. Mantén la veracidad, precisión y calidad informativa; "
                    "la personalidad cambia únicamente la forma de expresarte. No incluyas insultos, amenazas ni "
                    "agresiones al usuario. Mantén código, consultas, datos estructurados y formato técnico exactos.\n\n"
                    f"Personalidad seleccionada: {TONOS[pregunta.tono]['instruccion']}\n"
                    + ("Los emojis están permitidos con moderación y deben complementar el texto, nunca sustituir palabras."
                       if pregunta.usar_emojis else "No utilices emojis en la respuesta, independientemente de la personalidad seleccionada.")
                ),
                tools=HERRAMIENTAS_GEMINI,
            ),
        )

        texto_respuesta = respuesta.text or "No se generó una respuesta."
        guardar_mensaje(conversacion_id, "model", texto_respuesta)
        return {
            "respuesta": texto_respuesta,
            "conversacion_id": conversacion_id,
            "tono": pregunta.tono,
            "usar_emojis": pregunta.usar_emojis,
        }

    except HTTPException:
        raise
    except MySQLError as error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar la base de datos. Verifica su disponibilidad y configuración."
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible completar la consulta al asistente. Revisa la configuración de Gemini."
        ) from error


@router.get("/conversaciones")
def consultar_conversaciones():
    """Devuelve las conversaciones disponibles para continuar."""
    try:
        return listar_conversaciones()
    except MySQLError as error:
        raise HTTPException(status_code=500, detail=f"Error al acceder a MySQL: {str(error)}")


@router.get("/tonos")
def consultar_tonos():
    """Devuelve los tonos disponibles para clientes de la API."""
    return {"tono_predeterminado": TONO_PREDETERMINADO, "tonos": listar_tonos()}


@router.put("/conversaciones/{conversacion_id}/preferencias")
def actualizar_preferencias(conversacion_id: str, preferencias: PreferenciasConversacion):
    """Actualiza tono y uso de emojis de una conversación ya guardada."""
    try:
        if not existe_conversacion(conversacion_id):
            raise HTTPException(status_code=404, detail="La conversación no existe.")
        actualizar_preferencias_conversacion(conversacion_id, preferencias.tono, preferencias.usar_emojis)
        return {"tono": preferencias.tono, "usar_emojis": preferencias.usar_emojis}
    except HTTPException:
        raise
    except MySQLError as error:
        raise HTTPException(status_code=500, detail="No fue posible guardar las preferencias de la conversación.") from error


@router.get("/conversaciones/{conversacion_id}")
def consultar_conversacion(conversacion_id: str):
    """Devuelve una conversación junto con todos sus mensajes."""
    try:
        conversacion = obtener_conversacion(conversacion_id)
        if conversacion is None:
            raise HTTPException(status_code=404, detail="La conversación no existe.")
        return conversacion
    except HTTPException:
        raise
    except MySQLError as error:
        raise HTTPException(status_code=500, detail=f"Error al acceder a MySQL: {str(error)}")


@router.delete("/conversaciones/{conversacion_id}")
def borrar_conversacion(conversacion_id: UUID):
    """Elimina una conversación y sus mensajes asociados."""
    try:
        if not eliminar_conversacion(str(conversacion_id)):
            raise HTTPException(status_code=404, detail="La conversación no existe.")
        return {
            "mensaje": "La conversación se eliminó correctamente.",
            "conversacion_id": str(conversacion_id),
        }
    except HTTPException:
        raise
    except MySQLError as error:
        raise HTTPException(status_code=500, detail=f"Error al acceder a MySQL: {str(error)}")
