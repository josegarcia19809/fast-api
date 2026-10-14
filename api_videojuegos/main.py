from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

videojuegos = [
    {"id": 1, "nombre": "Minecraft", "plataforma": "PC"},
    {"id": 2, "nombre": "Mario Kart", "plataforma": "Nintendo"},
    {"id": 3, "nombre": "God of War", "plataforma": "PlayStation"},
]


@app.get("/api/videojuegos")
def obtener_videojuegos():
    return videojuegos