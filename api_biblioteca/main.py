from fastapi import FastAPI, Depends
from core.security import oauth2_scheme

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


@app.get("/me")
def read_user(
        user: dict = Depends(get_fake_user) # Aqui se manda llamar a la dependencia
):
    return {
        "user": user
    }

@app.get("/secure")
def secure_endpoint(token: str = Depends(oauth2_scheme)):
    return {"message": "Acceso con token", "token_recibido": token}