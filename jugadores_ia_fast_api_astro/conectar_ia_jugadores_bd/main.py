from fastapi import FastAPI

from routers import jugadores, clubes, chat
from database import inicializar_base_datos
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="API de Jugadores con Gemini",
    description="API de estadísticas de fútbol con asistente de IA y Tool Calling",
    version="1.1.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

app.include_router(jugadores.router)
app.include_router(clubes.router)
app.include_router(chat.router)


@app.on_event("startup")
def preparar_base_datos():
    inicializar_base_datos()


@app.get("/")
def inicio():
    return {"mensaje": "API de jugadores con Gemini"}
