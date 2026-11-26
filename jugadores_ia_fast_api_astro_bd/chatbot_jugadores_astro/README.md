# Chatbot Astro + FastAPI

Interfaz independiente en Astro para consumir el backend FastAPI incluido en el ZIP original.

## Requisitos
- Node.js 22 o superior (recomendado una versión LTS compatible con Astro 5).
- Backend FastAPI en ejecución y base de datos configurada.

## Instalación
```bash
npm install
cp .env.example .env
# Ajusta PUBLIC_API_URL si FastAPI está en otra dirección
npm run dev
```
Abre http://localhost:4321.

## API utilizada
Según el código FastAPI recibido:
- `POST /api/chat` con `{ "mensaje": "...", "conversacion_id": "opcional" }`.
- `GET /api/conversaciones` para listar el historial.
- `GET /api/conversaciones/{conversacion_id}` para recuperar mensajes.
- `DELETE /api/conversaciones/{conversacion_id}` para eliminar una conversación.
- `GET /` como comprobación básica del backend.

La respuesta de chat esperada es `{ "respuesta": "...", "conversacion_id": "uuid" }`.
El frontend conserva el identificador devuelto para continuar la misma conversación.

## CORS
El `main.py` entregado ya permite `http://localhost:4321` y `http://127.0.0.1:4321`. Si cambias el host o puerto de Astro, agrega ese origen en `allow_origins` de FastAPI.

## Markdown
Las respuestas se muestran con `marked` y se sanitizan con DOMPurify antes de insertarse en la interfaz.

## Notas
El frontend no contiene credenciales de Gemini ni de MySQL. La clave de Gemini permanece exclusivamente en FastAPI.
