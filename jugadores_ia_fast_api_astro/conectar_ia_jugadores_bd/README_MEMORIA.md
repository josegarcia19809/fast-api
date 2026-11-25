# Memoria conversacional con Gemini y MySQL

## 1. Configuración

1. Crea la base `mundial_fifa_2026` y las tablas `clubes` y `jugadores` ejecutando `jugadores_clubes_tabla.sql` en MySQL. La estructura debe estar cargada antes de iniciar FastAPI.
2. Copia `.env.example` a `.env`.
3. Configura `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_HISTORY_LIMIT` y las credenciales `MYSQL_*` en `.env`.
4. Instala las dependencias con `pip install -r requirements.txt`.
5. Inicia FastAPI con `uvicorn main:app --reload`. Al arrancar, la aplicación crea automáticamente las tablas `conversaciones` y `mensajes` si no existen.

La base de datos indicada por `MYSQL_DATABASE` debe existir previamente. El valor predeterminado es `mundial_fifa_2026`. El usuario de MySQL debe tener permisos para crear las tablas de memoria conversacional.

## 2. Consultas inteligentes sobre jugadores y clubes

El endpoint `POST /api/chat` dispone de herramientas Python controladas para consultar los campos existentes en `jugadores` y `clubes`. Gemini decide cuál usar y responde exclusivamente con los resultados de MySQL. Las búsquedas parametrizan sus filtros, las consultas combinadas usan `JOIN`, las estadísticas se calculan en MySQL y las listas de jugadores se limitan a 100 resultados. No se ejecuta SQL generado por el usuario.

Las 33 herramientas solicitadas están registradas, además de las existentes para recuperar imágenes, estadísticas globales, información de un club y comparación de jugadores:

- **Jugadores:** `consultar_jugadores`, `buscar_jugador`, `consultar_jugadores_por_edad`, `consultar_jugadores_por_numero`, `consultar_jugadores_ordenados`.
- **Nacionalidad y posición:** `consultar_por_nacionalidad`, `consultar_nacionalidades`, `consultar_por_posicion`, `consultar_cantidad_por_posicion`, `consultar_promedio_edad_por_posicion`.
- **Características físicas:** `consultar_jugador_mas_alto`, `consultar_jugador_mas_bajo`, `consultar_jugador_mas_pesado`, `consultar_promedios_fisicos`, `consultar_por_pie_dominante`.
- **Valor de mercado:** `consultar_jugador_mas_valioso`, `consultar_jugador_menos_valioso`, `consultar_valor_total_mercado`, `consultar_promedio_valor_mercado`, `consultar_jugadores_por_valor`, `consultar_valor_mercado_por_nacionalidad`.
- **Clubes:** `consultar_clubes`, `buscar_club`, `consultar_clubes_por_pais`, `consultar_clubes_por_liga`, `consultar_jugadores_por_club`, `consultar_cantidad_jugadores_por_club`.
- **Consultas combinadas:** `consultar_jugadores_por_liga`, `consultar_valor_mercado_por_liga`, `consultar_estadisticas_por_club`, `consultar_jugadores_por_pais_club`, `comparar_clubes`, `consultar_jugadores_por_antiguedad_club`.

Los valores de mercado se expresan en millones de euros según los datos proporcionados. No hay campos de goles, asistencias, partidos, minutos ni tarjetas.

El registro completo está en `routers/chat_tools.py` (`HERRAMIENTAS_GEMINI`). La imagen proviene de `jugadores.imagen`; para mostrarse inline debe contener una URL accesible al cliente.

## 3. Endpoints de conversación

### Enviar un mensaje e iniciar una conversación

`POST /api/chat`

```json
{
  "mensaje": "¿Quién es el jugador con mayor valor de mercado?"
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
  "mensaje": "¿Qué nacionalidad tiene?",
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

## 4. Ejemplos para probar desde Swagger

Inicia la aplicación y abre `http://localhost:8000/docs`. Envía estas preguntas a `POST /api/chat`:

- `Muéstrame los jugadores franceses.`
- `¿Qué jugadores del Real Madrid tienen entre 20 y 29 años?`
- `¿Cuántos mediocampistas hay por posición?`
- `¿Cuál es el valor total de mercado de los jugadores?`
- `¿Qué jugadores juegan en la Premier League?`
- `Compara al Real Madrid con el Manchester City.`
- `¿Qué jugadores son zurdos?`
- `¿Qué clubes tienen más de un jugador registrado?`
- `¿Cuál es el jugador más alto y cuál es el más pesado?`
- `¿Qué jugadores pertenecen a clubes fundados antes de 1900?`

Puedes continuar una conversación enviando el `conversacion_id` devuelto. Por ejemplo: `¿Cuáles de ellos son franceses?`; Gemini usa el historial para interpretar la referencia y vuelve a consultar MySQL.

## 5. Persistencia

- `conversaciones`: identifica cada sesión y guarda su título y fechas.
- `mensajes`: almacena cada mensaje con su rol (`user` o `model`), contenido y fecha.
- Las conversaciones se conservan al reiniciar FastAPI porque los datos residen en MySQL.

## 6. Endpoints REST de consultas

Las consultas disponibles en el chat también se exponen como endpoints GET bajo `/jugadores` y `/clubes`. Los filtros de texto van en la ruta o como parámetros de consulta; FastAPI devuelve HTTP 422 para parámetros inválidos y HTTP 500 si MySQL falla.

### Jugadores

- `GET /jugadores` — lista jugadores.
- `GET /jugadores/buscar?nombre=...`, `GET /jugadores/imagen?nombre=...`.
- `GET /jugadores/por-edad?edad_minima=20&edad_maxima=29`, `/jugadores/por-numero/{numero}`, `/jugadores/ordenados?criterio=edad`.
- `GET /jugadores/por-nacionalidad/{nacionalidad}`, `/jugadores/nacionalidades`, `/jugadores/por-posicion/{posicion}`, `/jugadores/por-pie/{pie}`.
- `GET /jugadores/cantidad-por-posicion`, `/jugadores/promedio-edad-por-posicion`, `/jugadores/estadisticas`.
- `GET /jugadores/mas-alto`, `/jugadores/mas-bajo`, `/jugadores/mas-pesado`, `/jugadores/promedios-fisicos`.
- `GET /jugadores/mas-valioso`, `/jugadores/menos-valioso`, `/jugadores/valor-mercado/total`, `/jugadores/valor-mercado/promedio`, `/jugadores/valor-mercado/por-nacionalidad`.
- `GET /jugadores/por-valor?valor_minimo=10&valor_maximo=50`.
- `GET /jugadores/por-club/{club}?posicion=...`, `/jugadores/por-liga/{liga}`, `/jugadores/por-pais-del-club/{pais}`, `/jugadores/por-antiguedad-del-club/{anio}`.
- `GET /jugadores/comparar?jugador_1=...&jugador_2=...`.

### Clubes

- `GET /clubes`, `GET /clubes/buscar?nombre=...`, `GET /clubes/nombre/{nombre}`.
- `GET /clubes/por-pais/{pais}`, `/clubes/por-liga/{liga}`.
- `GET /clubes/estadisticas`, `/clubes/cantidad-de-jugadores`, `/clubes/valor-mercado/por-liga`, `/clubes/valor-mercado/ranking`.
- `GET /clubes/comparar?club_1=...&club_2=...`.
- `GET /clubes/{id_club}` y `GET /clubes/{id_club}/jugadores?posicion=...` conservan las consultas existentes por ID.

La documentación interactiva de todas las rutas está disponible en `/docs` al iniciar FastAPI. Las rutas previas `/jugadores/posicion/{posicion}`, `/jugadores/cantidad/{posicion}` y `/jugadores/numero/{numero}` siguen disponibles por compatibilidad.
