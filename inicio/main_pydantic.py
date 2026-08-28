from fastapi import FastAPI, Query, Body, HTTPException, Path, status
from pydantic import BaseModel
from typing import Optional

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


class PostBase(BaseModel):
    title: str
    content: Optional[str] = "Contenido no disponible"


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str
    content: Optional[str] = None


@app.get("/")
def home():
    return {"Hola": "Mundo"}


# http://127.0.0.1:8000/posts
@app.get("/posts")
def list_posts():
    return {"data": BLOG_POST}


# http://127.0.0.1:8000/list-posts?query=Python
@app.get("/list-posts")
def list_posts(query: str | None = Query(default=None,
                                         description="Texto para buscar por tìtulo")):
    if query:
        results = []
        for post in BLOG_POST:
            if query.lower() in post["title"].lower():
                results.append(post)

        return {"data": results, "query": query}
    return {"data": BLOG_POST}


# http://127.0.0.1:8000/posts/2
@app.get("/posts/{post_id}")
def list_posts(post_id: int):
    for post in BLOG_POST:
        if post_id == post["id"]:
            return {"data": post}
    return {"error": "Post no encontrado"}


# http://127.0.0.1:8000/lista-posts/2?include_content=True
@app.get("/lista-posts/{post_id}")
def list_posts(post_id: int,
               include_content: bool = Query(default=True,
                                             description="Incluir o no el contenido")):
    for post in BLOG_POST:
        if post_id == post["id"]:
            post_response = post.copy()

            if not include_content:
                post_response.pop("content")

            return {"data": post_response}
    return {"error": "Post no encontrado"}


@app.post("/posts")
def create_post(post: PostCreate):
    # Generar nuevo ID
    new_id = len(BLOG_POST) + 1

    new_post = {
        "id": new_id,
        "title": post.title,
        "content": post.content
    }

    BLOG_POST.append(new_post)

    return {
        "message": "Post creado correctamente",
        "data": new_post
    }


@app.put("/posts/{post_id}")
def update_post(post_id: int, data: PostUpdate):
    # Buscar el post
    for post in BLOG_POST:

        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True)
            # Actualizar el post
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]

            return {
                "message": "Post actualizado correctamente",
                "data": post
            }

    # Si no encontramos el post
    raise HTTPException(
        status_code=404,
        detail="Post no encontrado"
    )


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
        post_id: int = Path(..., description="ID del post a eliminar")
):
    # Buscar el post
    for post in BLOG_POST:

        if post["id"] == post_id:
            # Eliminar el post
            BLOG_POST.remove(post)

            return

    # Si no encontramos el post
    raise HTTPException(
        status_code=404,
        detail="Post no encontrado"
    )
