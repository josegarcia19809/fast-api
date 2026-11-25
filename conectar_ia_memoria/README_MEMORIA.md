# Memoria conversacional con Gemini y MySQL

## 1. Configuración

1. Crea la base de datos ejecutando `base_datos.sql` en MySQL (por ejemplo, desde MySQL Workbench o la consola).
2. Copia `.env.example` a `.env`.
3. Configura `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_HISTORY_LIMIT` y las credenciales `MYSQL_*` en `.env`.
4. Instala las dependencias de `requirements.txt`.
5. Inicia FastAPI como lo hacías habitualmente. Al arrancar, la aplicación crea automáticamente las tablas `conversaciones` y `mensajes` si no existen.

La base de datos indicada por `MYSQL_DATABASE` debe existir previamente. El usuario de MySQL debe tener permisos para crear y modificar tablas.

## 2. Endpoints de conversación

### Enviar un mensaje e iniciar una conversación

`POST /api/chat`

```json
{
  "mensaje": "¿Quién tiene más goles?"
}
```

La respuesta incluye el identificador que debes conservar para los siguientes mensajes:

```json
{
  "respuesta": "...",
  "conversacion_id": "uuid-de-la-conversacion"
}
```

### Continuar una conversación existente

Envía el mismo endpoint incluyendo el identificador recibido:

```json
{
  "mensaje": "¿Y cuántos goles tiene el segundo?",
  "conversacion_id": "uuid-de-la-conversacion"
}
```

Gemini recibe como máximo los últimos `GEMINI_HISTORY_LIMIT` mensajes en orden cronológico. El valor predeterminado es `10`. El historial completo permanece almacenado en MySQL.

### Listar conversaciones

`GET /api/conversaciones`

Devuelve el identificador, título, fechas y cantidad de mensajes de cada conversación.

### Recuperar una conversación

`GET /api/conversaciones/{conversacion_id}`

Devuelve los datos de la conversación y sus mensajes. Si el identificador no existe, responde con HTTP 404.

Para cambiar el límite, define por ejemplo `GEMINI_HISTORY_LIMIT=20` en `.env` y reinicia FastAPI. La variable solo controla el contexto enviado a Gemini; no limita el historial que devuelve este endpoint.

## 3. Persistencia

- `conversaciones`: identifica cada sesión y guarda su título y fechas.
- `mensajes`: almacena cada mensaje con su rol (`user` o `model`), contenido y fecha.
- Las conversaciones se conservan al reiniciar FastAPI porque los datos residen en MySQL.
