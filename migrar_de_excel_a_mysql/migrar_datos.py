"""Migra jugadores y clubes desde el libro Excel del proyecto a MySQL."""

from __future__ import annotations

import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import mysql.connector
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_EXCEL = BASE_DIR / "jugadores_mundial_fifa_2026.xlsx"

# Nombres comprobados en la hoja "Jugadores" del archivo del proyecto.
PLAYER_COLUMNS = (
    "nombre", "apellido", "edad", "nacionalidad", "posicion",
    "numero_camiseta", "valor_mercado", "altura", "peso",
    "pie_dominante", "imagen",
)
CLUB_COLUMNS = ("nombre_club", "pais_club", "liga", "estadio", "anio_fundacion")
REQUIRED_COLUMNS = (*PLAYER_COLUMNS, *CLUB_COLUMNS)

# DDL alineado con estructura_jugadores_clubes.sql. MySQL confirma el DDL
# implícitamente, por eso se ejecuta antes de abrir la transacción de datos.
CREATE_TABLES = (
    """CREATE TABLE IF NOT EXISTS clubes (
        id_club INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        pais VARCHAR(60) NOT NULL,
        liga VARCHAR(80) NOT NULL,
        estadio VARCHAR(100),
        anio_fundacion INT,
        UNIQUE KEY uq_clubes_nombre (nombre)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS jugadores (
        id_jugador INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(60) NOT NULL,
        apellido VARCHAR(60) NOT NULL,
        edad INT,
        nacionalidad VARCHAR(60),
        posicion VARCHAR(30),
        numero_camiseta INT,
        valor_mercado DECIMAL(12,2),
        altura DECIMAL(3,2),
        peso DECIMAL(5,2),
        pie_dominante VARCHAR(15),
        imagen VARCHAR(500),
        id_club INT NOT NULL,
        CONSTRAINT fk_jugadores_clubes FOREIGN KEY (id_club)
            REFERENCES clubes(id_club)
            ON UPDATE CASCADE ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
)


def clean_value(value: Any) -> Any:
    """Convierte celdas vacías de pandas a None y limpia texto."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def as_int(value: Any, field: str) -> int | None:
    value = clean_value(value)
    if value is None:
        return None
    number = Decimal(str(value))
    if number != number.to_integral_value():
        raise ValueError(f"{field} debe ser un número entero: {value}")
    return int(number)


def as_decimal(value: Any, field: str) -> Decimal | None:
    value = clean_value(value)
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field} no es un número válido: {value}") from exc


def load_excel(excel_path: Path) -> pd.DataFrame:
    if not excel_path.is_file():
        raise FileNotFoundError(f"No existe el archivo Excel: {excel_path}")
    frame = pd.read_excel(excel_path, sheet_name="Jugadores", engine="openpyxl")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("Faltan columnas requeridas en la hoja 'Jugadores': " + ", ".join(missing))
    return frame


def database_config() -> dict[str, Any]:
    load_dotenv(BASE_DIR / ".env")
    required = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    missing = [key for key in required if os.getenv(key) is None]
    if missing:
        raise ValueError("Configura estas variables en .env: " + ", ".join(missing))
    return {
        "host": os.environ["MYSQL_HOST"],
        "port": int(os.environ["MYSQL_PORT"]),
        "user": os.environ["MYSQL_USER"],
        "password": os.environ["MYSQL_PASSWORD"],
        "database": os.environ["MYSQL_DATABASE"],
    }


def find_club_id(cursor: Any, name: str) -> int | None:
    """Busca el club por nombre para reutilizarlo en ejecuciones posteriores."""
    cursor.execute(
        "SELECT id_club FROM clubes WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
        (name,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def player_already_imported(cursor: Any, values: dict[str, Any], club_id: int) -> bool:
    """Considera duplicado al jugador con los mismos campos importados y club."""
    params = tuple(values[field] for field in PLAYER_COLUMNS) + (club_id,)
    cursor.execute(
        """SELECT 1 FROM jugadores WHERE nombre=%s AND apellido=%s
           AND edad <=> %s AND nacionalidad <=> %s AND posicion <=> %s
           AND numero_camiseta <=> %s AND valor_mercado <=> %s AND altura <=> %s
           AND peso <=> %s AND pie_dominante <=> %s AND imagen <=> %s AND id_club=%s
           LIMIT 1""",
        params,
    )
    return cursor.fetchone() is not None


def migrate(excel_path: Path = DEFAULT_EXCEL) -> dict[str, Any]:
    frame = load_excel(excel_path)
    # Mantiene una única ficha por nombre de club, ignorando diferencias de espacios/mayúsculas.
    clubs: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for excel_row, row in enumerate(frame.to_dict(orient="records"), start=2):
        club_name = clean_value(row.get("nombre_club"))
        if club_name is None:
            errors.append(f"Fila {excel_row}: falta nombre_club; jugador omitido.")
            continue
        key = str(club_name).casefold()
        clubs.setdefault(key, {
            "nombre": club_name,
            "pais": clean_value(row.get("pais_club")),
            "liga": clean_value(row.get("liga")),
            "estadio": clean_value(row.get("estadio")),
            "anio_fundacion": as_int(row.get("anio_fundacion"), "anio_fundacion"),
        })

    counts = {"clubes_identificados": len(clubs), "clubes_insertados": 0,
              "jugadores_procesados": len(frame), "jugadores_insertados": 0,
              "omitidos_duplicidad": 0, "errores": errors}
    connection = mysql.connector.connect(**database_config())
    cursor = None
    try:
        cursor = connection.cursor()
        for statement in CREATE_TABLES:
            cursor.execute(statement)
        connection.start_transaction()
        club_ids: dict[str, int] = {}
        for key, club in clubs.items():
            existing_id = find_club_id(cursor, club["nombre"])
            if existing_id is not None:
                club_ids[key] = existing_id
                continue
            if not club["pais"] or not club["liga"]:
                raise ValueError(f"El club '{club['nombre']}' requiere pais_club y liga (NOT NULL).")
            cursor.execute(
                "INSERT INTO clubes (nombre, pais, liga, estadio, anio_fundacion) VALUES (%s, %s, %s, %s, %s)",
                (club["nombre"], club["pais"], club["liga"], club["estadio"], club["anio_fundacion"]),
            )
            club_ids[key] = cursor.lastrowid
            counts["clubes_insertados"] += 1

        for excel_row, row in enumerate(frame.to_dict(orient="records"), start=2):
            values = {field: clean_value(row.get(field)) for field in PLAYER_COLUMNS}
            club_name = clean_value(row.get("nombre_club"))
            if not values["nombre"] or not values["apellido"] or not club_name:
                errors.append(f"Fila {excel_row}: faltan nombre, apellido o club; jugador omitido.")
                continue
            try:
                values["edad"] = as_int(values["edad"], "edad")
                values["numero_camiseta"] = as_int(values["numero_camiseta"], "numero_camiseta")
                for field in ("valor_mercado", "altura", "peso"):
                    values[field] = as_decimal(values[field], field)
            except (ValueError, InvalidOperation) as exc:
                errors.append(f"Fila {excel_row}: {exc}; jugador omitido.")
                continue
            club_id = club_ids.get(str(club_name).casefold())
            if club_id is None:
                errors.append(f"Fila {excel_row}: no se pudo asociar el club '{club_name}'.")
                continue
            if player_already_imported(cursor, values, club_id):
                counts["omitidos_duplicidad"] += 1
                continue
            params = tuple(values[field] for field in PLAYER_COLUMNS) + (club_id,)
            cursor.execute(
                """INSERT INTO jugadores
                   (nombre, apellido, edad, nacionalidad, posicion, numero_camiseta,
                    valor_mercado, altura, peso, pie_dominante, imagen, id_club)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                params,
            )
            counts["jugadores_insertados"] += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
    return counts


def main() -> int:
    excel_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_EXCEL
    if not excel_path.is_absolute():
        excel_path = (Path.cwd() / excel_path).resolve()
    try:
        result = migrate(excel_path)
    except Exception as exc:
        print(f"Error en la migración; se revirtió la transacción: {exc}", file=sys.stderr)
        return 1
    print("Resumen de migración")
    print(f"Clubes identificados: {result['clubes_identificados']}")
    print(f"Clubes insertados: {result['clubes_insertados']}")
    print(f"Jugadores procesados: {result['jugadores_procesados']}")
    print(f"Jugadores insertados: {result['jugadores_insertados']}")
    print(f"Registros omitidos por duplicidad: {result['omitidos_duplicidad']}")
    print(f"Errores encontrados: {len(result['errores'])}")
    for error in result["errores"]:
        print(f"- {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
