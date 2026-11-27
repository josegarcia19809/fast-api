# Chatbot Astro + FastAPI

Interfaz independiente en Astro para consumir el backend FastAPI incluido en el ZIP original.

## Requisitos
- Node.js 22 o superior (recomendado una versión LTS compatible con Astro 5).
- Backend FastAPI en ejecución y base de datos configurada.
- Node.js para servir Astro mediante el adaptador oficial `@astrojs/node`.

## Instalación
```bash
npm install
cp .env.example .env
# Ajusta PUBLIC_API_URL si FastAPI está en otra dirección
npm run dev
```
Abre http://localhost:4321.

La navegación ofrece `/` (dashboard), `/clubes`, `/jugadores`, `/estadisticas` y `/chat` (el chatbot existente). Configura `PUBLIC_API_URL` en `.env` si FastAPI no está en `http://127.0.0.1:8000`.

Las páginas de edición usan renderizado dinámico en servidor. En producción compila con `npm run build` y ejecuta `npm run start` (sirve `dist/server/entry.mjs`); en desarrollo continúa disponible `npm run dev`.

## API utilizada
Según el código FastAPI recibido:
- `GET /api/tonos` para cargar tonos, nombres y descripciones.
- `POST /api/chat` con `{ "mensaje": "...", "conversacion_id": "opcional", "tono": "furioso", "usar_emojis": true }`.
- `GET /api/conversaciones` para listar el historial.
- `GET /api/conversaciones/{conversacion_id}` para recuperar mensajes.
- `DELETE /api/conversaciones/{conversacion_id}` para eliminar una conversación.
- `GET /` como comprobación básica del backend.

El panel también consume `GET /clubes/administracion`, `GET /jugadores/administracion` (paginado y filtrable), además de los métodos `POST`, `PUT` y `DELETE` de clubes y jugadores. Las estadísticas usan las rutas GET existentes de `/clubes/estadisticas`, `/jugadores/estadisticas` y `/jugadores/cantidad-por-posicion`.

La respuesta de chat incluye `{ "respuesta": "...", "conversacion_id": "uuid", "tono": "furioso", "usar_emojis": true }`.
El frontend conserva el identificador devuelto para continuar la misma conversación.
El selector permite elegir entre amigable, furioso, triste y amargado, además de activar o desactivar emojis. Ambas preferencias se conservan al reabrir una conversación y también pueden actualizarse mediante `PUT /api/conversaciones/{id}/preferencias`.

## CORS
El `main.py` entregado ya permite `http://localhost:4321` y `http://127.0.0.1:4321`. Si cambias el host o puerto de Astro, agrega ese origen en `allow_origins` de FastAPI.

## Markdown
Las respuestas se muestran con `marked` y se sanitizan con DOMPurify antes de insertarse en la interfaz.

## Notas
El frontend no contiene credenciales de Gemini ni de MySQL. La clave de Gemini permanece exclusivamente en FastAPI.
