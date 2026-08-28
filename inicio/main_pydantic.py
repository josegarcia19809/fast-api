from fastapi import FastAPI, Query, Body, HTTPException, Path, status
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Union

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

class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30, description="Nombre de la etiqueta")

class Author(BaseModel):
    name: str
    email: EmailStr

class PostBase(BaseModel):
    title: str
    content: Optional[str] = "Contenido no disponible"
    tags: Optional[List[Tag]] = []
    author: Optional[Author] = {"name": "", "email": ""}


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        description="Titulo para crear un post",
        min_length=3,
        max_length=100,
        examples=["Mi primer post con Fast API"]
    )
    content: Optional[str] = Field(
        default="Contenido no disponible",
        description="Contenido para crear un post",
        min_length=10,
        examples=["Este es un contenido válido"]
    )
    tags: List[Tag] = []
    author: Optional[Author] = {"name": "", "email": ""}

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        if "spam" in value.lower():
            raise ValueError("Titulo no valido")
        return value


class PostUpdate(BaseModel):
    title: str
    content: Optional[str] = None


class PostPublic(PostBase):
    id: int


class PostSummary(BaseModel):
    id: int
    title: str


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


# http://127.0.0.1:8000/list-posts2
@app.get("/list-posts2", response_model=List[PostPublic])
def list_posts2(query: str | None = Query(default=None,
                                          description="Texto para buscar por tìtulo")):
    if query:
        return [post for post in BLOG_POST if query.lower() in post["title"].lower()]
    return BLOG_POST


# http://127.0.0.1:8000/posts/2
@app.get("/posts/{post_id}")
def list_posts(post_id: int):
    for post in BLOG_POST:
        if post_id == post["id"]:
            return {"data": post}
    return {"error": "Post no encontrado"}


# http://127.0.0.1:8000/lista-posts/2?include_content=True
@app.get("/lista-posts/{post_id}")
def list_posts2(post_id: int,
                include_content: bool = Query(default=True,
                                              description="Incluir o no el contenido")):
    for post in BLOG_POST:
        if post_id == post["id"]:
            post_response = post.copy()

            if not include_content:
                post_response.pop("content")

            return {"data": post_response}
    return {"error": "Post no encontrado"}

# http://127.0.0.1:8000/posts3/2?include_content=True
@app.get("/posts3/{post_id}", response_model=Union[PostPublic, PostSummary],
         response_description="Post encontrado")
def get_post3(post_id: int, include_content: bool = Query(default=True,
                                                         description="Incluir o no el contenido")):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return {"id": post["id"], "title": post["title"]}
            return post

    raise HTTPException(status_code=404, detail="Post no encontrado")

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



@app.post("/posts2", response_model=PostPublic, response_description="Post creado (OK)")
def create_post2(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"]+1) if BLOG_POST else 1
    new_post = {"id": new_id,
                "title": post.title,
                "content": post.content,
                }
    BLOG_POST.append(new_post)
    return new_post


@app.post("/posts3", response_model=PostPublic, response_description="Post creado (OK)")
def create_post3(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"]+1) if BLOG_POST else 1
    new_post = {"id": new_id,
                "title": post.title,
                "content": post.content,
                "tags": [tag.model_dump() for tag in post.tags],
                "author": post.author.model_dump() if post.author else None
                }
    BLOG_POST.append(new_post)
    return new_post

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


@app.put("/posts2/{post_id}", response_model=PostPublic,
         response_description="Post actualizado", response_model_exclude_none=True)
def update_post2(post_id: int, data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(
                exclude_unset=True)  # {"title": "Ricardo", "content": None}
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]
            return post

    raise HTTPException(status_code=404, detail="Post no encontrado")


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


