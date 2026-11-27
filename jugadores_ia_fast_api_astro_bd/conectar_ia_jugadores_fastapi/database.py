"""Acceso a MySQL y persistencia de conversaciones."""
import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    """Abre una conexión usando las variables definidas en .env."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "conectar_ia"),
        charset="utf8mb4",
        use_unicode=True,
    )


def consultar_todos(sql: str, parametros: tuple = ()) -> list:
    """Ejecuta un SELECT y devuelve filas como diccionarios."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def consultar_uno(sql: str, parametros: tuple = ()):
    """Ejecuta un SELECT y devuelve una fila como diccionario o None."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def ejecutar_modificacion(sql: str, parametros: tuple = ()) -> dict:
    """Ejecuta INSERT/UPDATE/DELETE parametrizado y devuelve sus metadatos."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        resultado = {"filas": cursor.rowcount, "id": cursor.lastrowid}
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def inicializar_base_datos():
    """Crea las tablas necesarias si todavía no existen."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                id CHAR(36) PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                creada_en DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                actualizada_en DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                    ON UPDATE CURRENT_TIMESTAMP(6)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                conversacion_id CHAR(36) NOT NULL,
                rol ENUM('user', 'model') NOT NULL,
                contenido LONGTEXT NOT NULL,
                creado_en DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                INDEX idx_mensajes_conversacion (conversacion_id, id),
                CONSTRAINT fk_mensajes_conversacion
                    FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Preferencias por conversación; migración compatible con la memoria existente.
        cursor.execute("SHOW COLUMNS FROM conversaciones LIKE 'tono'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE conversaciones ADD COLUMN tono VARCHAR(32) NOT NULL DEFAULT 'amigable'")
        cursor.execute("UPDATE conversaciones SET tono = 'amigable' WHERE tono NOT IN ('amigable', 'furioso', 'triste', 'amargado')")
        cursor.execute("SHOW COLUMNS FROM conversaciones LIKE 'usar_emojis'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE conversaciones ADD COLUMN usar_emojis BOOLEAN NOT NULL DEFAULT FALSE")
        conexion.commit()
    finally:
        conexion.close()


def crear_conversacion(conversacion_id: str, titulo: str, tono: str = "amigable", usar_emojis: bool = False):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO conversaciones (id, titulo, tono, usar_emojis) VALUES (%s, %s, %s, %s)",
            (conversacion_id, titulo[:255] or "Nueva conversación", tono, usar_emojis),
        )
        conexion.commit()
    finally:
        conexion.close()


def actualizar_preferencias_conversacion(conversacion_id: str, tono: str, usar_emojis: bool):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE conversaciones SET tono = %s, usar_emojis = %s WHERE id = %s", (tono, usar_emojis, conversacion_id))
        conexion.commit()
    finally:
        conexion.close()


def existe_conversacion(conversacion_id: str) -> bool:
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT 1 FROM conversaciones WHERE id = %s", (conversacion_id,))
        return cursor.fetchone() is not None
    finally:
        conexion.close()


def guardar_mensaje(conversacion_id: str, rol: str, contenido: str):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO mensajes (conversacion_id, rol, contenido) VALUES (%s, %s, %s)",
            (conversacion_id, rol, contenido),
        )
        cursor.execute(
            "UPDATE conversaciones SET actualizada_en = CURRENT_TIMESTAMP(6) WHERE id = %s",
            (conversacion_id,),
        )
        conexion.commit()
    finally:
        conexion.close()


def obtener_historial(conversacion_id: str, limite: int = 10) -> list:
    """Obtiene los mensajes recientes para el contexto de Gemini en orden cronológico."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT rol, contenido FROM ("
            "SELECT id, rol, contenido FROM mensajes "
            "WHERE conversacion_id = %s ORDER BY id DESC LIMIT %s"
            ") AS mensajes_recientes ORDER BY id",
            (conversacion_id, limite),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_conversaciones() -> list:
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, c.titulo, c.tono, c.usar_emojis, c.creada_en, c.actualizada_en,
                   COUNT(m.id) AS total_mensajes
            FROM conversaciones c
            LEFT JOIN mensajes m ON m.conversacion_id = c.id
            GROUP BY c.id, c.titulo, c.creada_en, c.actualizada_en
            ORDER BY c.actualizada_en DESC
        """)
        filas = cursor.fetchall()
        for fila in filas:
            fila["creada_en"] = fila["creada_en"].isoformat()
            fila["actualizada_en"] = fila["actualizada_en"].isoformat()
        return filas
    finally:
        conexion.close()


def obtener_conversacion(conversacion_id: str):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, titulo, tono, usar_emojis, creada_en, actualizada_en FROM conversaciones WHERE id = %s",
            (conversacion_id,),
        )
        conversacion = cursor.fetchone()
        if conversacion is None:
            return None
        cursor.execute(
            "SELECT id, rol, contenido, creado_en FROM mensajes "
            "WHERE conversacion_id = %s ORDER BY id",
            (conversacion_id,),
        )
        conversacion["mensajes"] = cursor.fetchall()
        conversacion["creada_en"] = conversacion["creada_en"].isoformat()
        conversacion["actualizada_en"] = conversacion["actualizada_en"].isoformat()
        for mensaje in conversacion["mensajes"]:
            mensaje["creado_en"] = mensaje["creado_en"].isoformat()
        return conversacion
    finally:
        conexion.close()


def eliminar_conversacion(conversacion_id: str) -> bool:
    """Elimina una conversación; MySQL elimina sus mensajes mediante ON DELETE CASCADE."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM conversaciones WHERE id = %s", (conversacion_id,))
        eliminada = cursor.rowcount > 0
        if eliminada:
            conexion.commit()
        return eliminada
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
