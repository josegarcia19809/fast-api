from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def inicio():
    return {
        "mensaje": "API de libros funcionando"
    }


@app.get("/libro/{isbn}")
def mostrar_libro(isbn: int):
    return {
        "isbn": isbn,
        "titulo": "el principito",
        "autor": "antoine-de-saint"
    }
