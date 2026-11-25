import os
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from mysql.connector import Error as MySQLError
from pydantic import BaseModel
from google import genai
from google.genai import types

from routers.jugadores import jugadores
from database import (
    crear_conversacion, existe_conversacion, guardar_mensaje,
    obtener_historial, listar_conversaciones, obtener_conversacion,
    eliminar_conversacion,
)

load_dotenv()

router = APIRouter(prefix="/api", tags=["chat"])


class Pregunta(BaseModel):
    mensaje: str
    conversacion_id: str | None = None


def listar_jugadores(posicion: str = "") -> list:
    """Consulta todos los jugadores o filtra por posición.

    Args:
        posicion: Posición a consultar: Delantero, Mediocampista o Defensor.
                  Déjala vacía para consultar todos.
    """
    if not posicion:
        return jugadores

    return [
        jugador for jugador in jugadores
        if jugador["posicion"].lower() == posicion.lower()
    ]


def obtener_goles_por_posicion(posicion: str) -> dict:
    """Obtiene el total de goles anotados por los jugadores de una posición.

    Args:
        posicion: Posición: Delantero, Mediocampista o Defensor.
    """
    total = sum(
        jugador["goles"] for jugador in jugadores
        if jugador["posicion"].lower() == posicion.lower()
    )
    return {"posicion": posicion, "total_goles": total}


def obtener_cantidad_por_posicion(posicion: str) -> dict:
    """Cuenta cuántos jugadores pertenecen a una posición.

    Args:
        posicion: Posición: Delantero, Mediocampista o Defensor.
    """
    cantidad = sum(
        1 for jugador in jugadores
        if jugador["posicion"].lower() == posicion.lower()
    )
    return {"posicion": posicion, "cantidad": cantidad}


def obtener_promedio_por_posicion(posicion: str) -> dict:
    """Calcula el promedio de goles de los jugadores de una posición.

    Args:
        posicion: Posición: Delantero, Mediocampista o Defensor.
    """
    grupo = [
        jugador for jugador in jugadores
        if jugador["posicion"].lower() == posicion.lower()
    ]
    promedio = sum(j["goles"] for j in grupo) / len(grupo) if grupo else 0
    return {"posicion": posicion, "promedio": round(promedio, 2)}


def buscar_jugador_por_numero(numero: int) -> dict:
    """Busca los datos de un jugador usando su número de camiseta.

    Args:
        numero: Número de camiseta del jugador.
    """
    for jugador in jugadores:
        if jugador["numero"] == numero:
            return jugador
    return {"error": f"No existe un jugador con el número {numero}."}


def filtrar_jugadores_por_goles(goles: int) -> list:
    """Devuelve los jugadores que tienen más goles que la cantidad indicada.

    Args:
        goles: Cantidad mínima de referencia; se buscan jugadores con más goles.
    """
    return [j for j in jugadores if j["goles"] > goles]


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
            crear_conversacion(conversacion_id, pregunta.mensaje)

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
                    "Eres un asistente de estadísticas de fútbol. "
                    "Responde siempre en español de México. "
                    "Usa las herramientas disponibles cuando necesites datos "
                    "de los jugadores. No inventes estadísticas: utiliza "
                    "los resultados de las herramientas. Ponle alegria a tus comentarios "
                    "y agrega emojis."
                ),
                tools=[
                    listar_jugadores,
                    obtener_goles_por_posicion,
                    obtener_cantidad_por_posicion,
                    obtener_promedio_por_posicion,
                    buscar_jugador_por_numero,
                    filtrar_jugadores_por_goles,
                ],
            ),
        )

        texto_respuesta = respuesta.text or "No se generó una respuesta."
        guardar_mensaje(conversacion_id, "model", texto_respuesta)
        return {
            "respuesta": texto_respuesta,
            "conversacion_id": conversacion_id,
        }

    except HTTPException:
        raise
    except MySQLError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al acceder a MySQL: {str(error)}. Verifica la configuración de la base de datos."
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar Gemini: {str(error)}"
        )


@router.get("/conversaciones")
def consultar_conversaciones():
    """Devuelve las conversaciones disponibles para continuar."""
    try:
        return listar_conversaciones()
    except MySQLError as error:
        raise HTTPException(status_code=500, detail=f"Error al acceder a MySQL: {str(error)}")


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
