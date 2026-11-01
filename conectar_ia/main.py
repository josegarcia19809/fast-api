
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

load_dotenv()

app = FastAPI()

cliente = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class Pregunta(BaseModel):
    mensaje: str

@app.post("/api/chat")
def consultar_gemini(pregunta: Pregunta)-> str | None:
    try:
        respuesta = cliente.interactions.create(
            model="gemini-3.5-flash",
            input=pregunta.mensaje
        )

        return respuesta.output_text

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

