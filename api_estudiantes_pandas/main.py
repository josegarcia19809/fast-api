
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

# Leer el archivo CSV
df = pd.read_csv("estudiantes.csv")


@app.get("/")
def inicio():
    return {"mensaje": "API de estudiantes con Pandas"}


# Consultar todos los estudiantes
@app.get("/estudiantes")
def consultar_estudiantes():
    return df.to_dict(orient="records")


# Consultar estudiantes aprobados
@app.get("/estudiantes/aprobados")
def estudiantes_aprobados():
    aprobados = df[df["calificacion"] >= 70]

    return aprobados.to_dict(orient="records")


# Consultar promedio del grupo
@app.get("/estudiantes/promedio")
def promedio_grupo():
    promedio = df["calificacion"].mean()

    return {"promedio": round(promedio, 2)}


# Filtrar estudiantes por edad
@app.get("/estudiantes/edad/{edad}")
def filtrar_por_edad(edad: int):
    resultado = df[df["edad"] == edad]

    return resultado.to_dict(orient="records")
