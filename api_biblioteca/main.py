from fastapi import FastAPI, Depends
from core.security import oauth2_scheme
from api.v1.auth.router import router as auth_router
from api.v1.libros.router import router as libros_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API de la Biblioteca",
    description="Consulta las publicaciones disponibles."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(libros_router, prefix="/api/v1")

