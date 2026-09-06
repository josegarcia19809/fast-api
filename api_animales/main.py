from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def index():
    return {
        "titulo": " 🐾 API de Animales",
        "autor": "José L. García"
    }


@app.get("/perro")
def mostrar_perro():
    return {
        "emoji": " 🐶 ",
        "animal": "Perro",
        "descripción": "Un amigo fiel"
    }


@app.get("/tigre")
def mostrar_tigre():
    return {
        "emoji": "🐅",
        "animal": "Tigre",
        "descripción": "Un desayuno de campeones"
    }