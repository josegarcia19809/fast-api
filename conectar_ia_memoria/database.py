"""Acceso a MySQL y persistencia de conversaciones."""
import os

import mysql.connector
from mysql.connector import Error


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
        conexion.commit()
    finally:
        conexion.close()


def crear_conversacion(conversacion_id: str, titulo: str):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO conversaciones (id, titulo) VALUES (%s, %s)",
            (conversacion_id, titulo[:255] or "Nueva conversación"),
        )
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


def obtener_historial(conversacion_id: str) -> list:
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT rol, contenido FROM mensajes WHERE conversacion_id = %s ORDER BY id",
            (conversacion_id,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_conversaciones() -> list:
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, c.titulo, c.creada_en, c.actualizada_en,
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
            "SELECT id, titulo, creada_en, actualizada_en FROM conversaciones WHERE id = %s",
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
