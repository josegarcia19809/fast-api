from fastapi import FastAPI

app = FastAPI(title="MINI BLOG")

BLOG_POST = [
    {
        "id": 1,
        "title": "Introducción a Python",
        "content": "Python es un lenguaje de programación fácil de aprender."
    },
    {
        "id": 2,
        "title": "Uso de Diccionarios",
        "content": "Los diccionarios almacenan datos en pares clave-valor."
    },
    {
        "id": 3,
        "title": "Listas en Python",
        "content": "Las listas permiten almacenar colecciones ordenadas de elementos."
    }
]


@app.get("/")
def home():
    return {"Hola": "Mundo"}

@app.get("/posts")
def list_posts():
    return {"data": BLOG_POST}