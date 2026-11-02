from fastapi import FastAPI, Depends
from core.security import oauth2_scheme
from api.v1.auth.router import router as auth_router
from api.v1.libros.router import router as libros_router


# Esta es la función que se va a inyectar como dependencia
def get_fake_user():
    return {
        "username": "marisol",
        "role": "admin"
    }


app = FastAPI(
    title="API de la Biblioteca",
    description="Consulta las publicaciones disponibles."
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(libros_router, prefix="/api/v1")

