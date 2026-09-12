from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def inicio():
    return {
        "mensaje": "API de la Librería"
    }

@app.get("/libro/recomendados")
def libros_recomendados():
    return {
        "mensaje": "Lista de libros recomendados"
    }

@app.get("/libro/mas-vendidos")
def libros_mas_vendidos():
    return {
        "mensaje": "Lista de libros más vendidos"
    }


@app.get("/libro/{id}")
def mostrar_libro(id: int):
    return {
        "id": id,
        "mensaje": f"Mostrando información del libro {id}"
    }


@app.get("/libro/isbn/{isbn}")
def buscar_por_isbn(isbn: str):
    return {
        "isbn": isbn
    }


@app.get("/autor/{nombre}")
def mostrar_autor(nombre: str):
    return {
        "autor": nombre
    }


@app.get("/autor/{autor_id}/libro/{libro_id}")
def mostrar_libro(autor_id: int, libro_id: int):
    return {
        "autor": autor_id,
        "libro": libro_id
    }


@app.get("/categoria/{nombre}")
def consultar_categoria(nombre: str):
    return {
        "categoria": nombre
    }


@app.get("/editorial/{id}")
def mostrar_editorial(id: int):
    return {
        "id": id,
        "mensaje": f"Mostrando editorial {id}"
    }
