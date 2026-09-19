from enum import Enum
from fastapi import FastAPI

app = FastAPI()


class TipoUsuario(str, Enum):
    ESTUDIANTE = "estudiante"
    PROFESOR = "profesor"
    ADMINISTRADOR = "administrador"


@app.get("/usuarios/{tipo_usuario}")
def obtener_usuario(tipo_usuario: TipoUsuario):
    return {
        "mensaje": f"Tipo de usuario: {tipo_usuario}"
    }
