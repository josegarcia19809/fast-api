from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    return Path("templates/index.html").read_text(
        encoding="utf-8"
    )

@app.get("/doctores/")
def index_doctores():
    return {
        "titulo": "👨‍⚕️ Doctores",
        "mensaje": "Hola, mundo. Bienvenido Doctor!"
    }

# 👨‍⚕️ Página principal para doctores
@app.get("/doctores/sistema-medico")
def sistema_medico():
    return {
        "titulo": "👨‍⚕️ Sistema Médico",
        "parrafos": [
            "Bienvenido Doctor al sistema de gestión hospitalaria.",
            "Desde aquí podrá acceder a sus pacientes y consultas."
        ]
    }


# 🧑‍🤝‍🧑 Vista de pacientes
@app.get("/doctores/pacientes")
def pacientes_doctor():
    return {
        "titulo": "🧑‍🤝‍🧑 Pacientes",
        "subtitulo": "Listado de pacientes",
        "parrafos": [
            "Consulta la información clínica de tus pacientes.",
            "Accede al historial médico y diagnósticos."
        ]
    }


# 📅 Vista de citas médicas
@app.get("/doctores/citas")
def citas_medicas():
    return {
        "titulo": "📅 Citas Médicas",
        "subtitulo": "Agenda del doctor",
        "parrafos": [
            "Revisa tus citas programadas.",
            "Organiza consultas presenciales y virtuales."
        ]
    }


# 📋 Vista de historial clínico
@app.get("/doctores/historial")
def historial_clinico():
    return {
        "titulo": "📋 Historial Clínico",
        "subtitulo": "Información médica",
        "parrafos": [
            "Consulta diagnósticos previos.",
            "Revisa tratamientos y resultados."
        ]
    }


# 💊 Vista de recetas médicas
@app.get("/doctores/recetas")
def recetas_medicas():
    return {
        "titulo": "💊 Recetas Médicas",
        "subtitulo": "Prescripción de medicamentos",
        "parrafos": [
            "Crea y consulta recetas para tus pacientes.",
            "Controla dosis y duración del tratamiento."
        ]
    }


# 🚑 Vista de emergencias
@app.get("/doctores/emergencias")
def emergencias():
    return {
        "titulo": "🚑 Emergencias",
        "subtitulo": "Atención prioritaria",
        "parrafos": [
            "Acceso rápido a pacientes en estado crítico.",
            "Protocolos de actuación inmediata."
        ]
    }
