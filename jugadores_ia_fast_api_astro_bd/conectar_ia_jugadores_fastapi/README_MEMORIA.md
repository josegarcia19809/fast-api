# Memoria conversacional con Gemini y MySQL

## 1. Configuración

1. Ejecuta `jugadores_clubes_tabla.sql` en MySQL para crear la base `conectar_ia` y las tablas `clubes` y `jugadores`. El esquema inicial incluye `jugadores.goles INT NOT NULL DEFAULT 0`. La estructura debe estar cargada antes de iniciar FastAPI.
2. Copia `.env.example` a `.env`.
3. Configura `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_HISTORY_LIMIT` y las credenciales `MYSQL_*` en `.env`.
4. Instala las dependencias con `pip install -r requirements.txt`.
5. Inicia FastAPI con `uvicorn main:app --reload`. Al arrancar, la aplicación crea automáticamente las tablas `conversaciones` y `mensajes` si no existen.

La base de datos indicada por `MYSQL_DATABASE` debe existir previamente. El valor predeterminado es `conectar_ia`. El usuario de MySQL debe tener permisos para crear las tablas de memoria conversacional.

## 2. Consultas inteligentes sobre jugadores y clubes

El endpoint `POST /api/chat` dispone de herramientas Python controladas para consultar los campos existentes en `jugadores` y `clubes`. Gemini decide cuál usar y responde exclusivamente con los resultados de MySQL. Las búsquedas parametrizan sus filtros, las consultas combinadas usan `JOIN`, las estadísticas se calculan en MySQL y las listas de jugadores se limitan a 100 resultados. No se ejecuta SQL generado por el usuario.

Las herramientas existentes para jugadores y clubes se conservan. También se registran Tools de defensas, mediocampistas, búsqueda por campos, detalle por ID y análisis de goles (cuando la columna está disponible):

- **Jugadores:** `consultar_jugadores`, `buscar_jugador`, `consultar_jugadores_por_edad`, `consultar_jugadores_por_numero`, `consultar_jugadores_ordenados`.
- **Nacionalidad y posición:** `consultar_por_nacionalidad`, `consultar_nacionalidades`, `consultar_por_posicion`, `consultar_cantidad_por_posicion`, `consultar_promedio_edad_por_posicion`.
- **Características físicas:** `consultar_jugador_mas_alto`, `consultar_jugador_mas_bajo`, `consultar_jugador_mas_pesado`, `consultar_promedios_fisicos`, `consultar_por_pie_dominante`.
- **Valor de mercado:** `consultar_jugador_mas_valioso`, `consultar_jugador_menos_valioso`, `consultar_valor_total_mercado`, `consultar_promedio_valor_mercado`, `consultar_jugadores_por_valor`, `consultar_valor_mercado_por_nacionalidad`.
- **Clubes:** `consultar_clubes`, `buscar_club`, `consultar_clubes_por_pais`, `consultar_clubes_por_liga`, `consultar_jugadores_por_club`, `consultar_cantidad_jugadores_por_club`.
- **Consultas combinadas:** `consultar_jugadores_por_liga`, `consultar_valor_mercado_por_liga`, `consultar_estadisticas_por_club`, `consultar_jugadores_por_pais_club`, `comparar_clubes`, `consultar_jugadores_por_antiguedad_club`.

Los valores de mercado se expresan en millones de euros según los datos proporcionados. La herramienta de goles comprueba `INFORMATION_SCHEMA.COLUMNS` antes de consultar `jugadores.goles`; si esa columna no existe, devuelve `disponible: false` sin calcular valores. Asistencias, partidos, minutos y tarjetas no se calculan porque no forman parte del esquema documentado.

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

## 7. Consultas nuevas de posiciones y goles

Las rutas agregadas se documentan también en Swagger con parámetros, descripciones y ejemplos. Las respuestas de jugadores contienen `j.*` más `club`, por lo que reflejan las columnas que realmente tiene `jugadores` en la base conectada.

### Jugadores

| Método y URL | Parámetros | Uso |
|---|---|---|
| `GET /jugadores/defensas` | Ninguno | Lista posiciones que contienen “defens” o usan `DF`/`DEF`. |
| `GET /jugadores/defensas/por-club` | `club` requerido | Filtra defensas por nombre parcial del club. |
| `GET /jugadores/defensas/por-seleccion` | `seleccion` requerido | Filtra defensas por `nacionalidad`, que representa la selección en este esquema. |
| `GET /jugadores/mediocampistas` | Ninguno | Reconoce mediocampista, centrocampista, medio, `MF` o `MED`. |
| `GET /jugadores/mediocampistas/por-club` | `club` requerido | Filtra mediocampistas por club. |
| `GET /jugadores/mediocampistas/por-seleccion` | `seleccion` requerido | Filtra mediocampistas por nacionalidad. |
| `GET /jugadores/buscar` | `nombre`, `apellido` y/o `posicion` opcionales | Combina los filtros indicados. Sigue aceptando la forma anterior `?nombre=...`. |
| `GET /jugadores/detalle/{id_jugador}` | `id_jugador` entero positivo | Devuelve todos los campos del jugador y el nombre de su club; responde 404 si no existe. |

Ejemplo de búsqueda desde Swagger: `GET /jugadores/buscar?apellido=Martínez&posicion=Defensa`. Ejemplo de respuesta (los atributos adicionales reflejan las columnas presentes):

```json
[
  {
    "id_jugador": 15,
    "nombre": "Lisandro",
    "apellido": "Martínez",
    "edad": 28,
    "nacionalidad": "Argentina",
    "posicion": "Defensa",
    "numero_camiseta": 6,
    "valor_mercado": 50.0,
    "altura": 1.75,
    "peso": 77.0,
    "pie_dominante": "Izquierdo",
    "imagen": null,
    "id_club": 4,
    "club": "Manchester United"
  }
]
```

### Goles y estadísticas

| Método y URL | Parámetros | Uso |
|---|---|---|
| `GET /jugadores/goles` | `limite` opcional (1–100, default 100), `posicion` opcional | Lista goles por jugador, descendente. |
| `GET /jugadores/goles/maximo-goleador` | `posicion` opcional | Devuelve la cifra máxima y todos los empates. |
| `GET /jugadores/goles/promedio` | `posicion` opcional | Devuelve conteo de jugadores con goles registrados, suma y promedio. |
| `GET /jugadores/goles/por-club` | Ninguno | Agrupa cantidad, suma y promedio por club. |
| `GET /jugadores/goles/por-seleccion` | Ninguno | Agrupa por `nacionalidad`. |
| `GET /jugadores/goles/comparar` | Repite `nombres` de 2 a 10 veces | Compara jugadores indicados: `?nombres=Lionel%20Messi&nombres=Kylian%20Mbappe`. |
| `GET /jugadores/estadisticas/por-posicion` | Ninguno | Agrupa cantidad y edad promedio; incluye goles solo cuando la columna existe. |

Cuando `goles` existe, una respuesta tiene esta forma:

```json
{
  "disponible": true,
  "cantidad": 2,
  "jugadores": [
    {"id_jugador": 1, "nombre": "Kylian", "apellido": "Mbappé", "goles": 10, "club": "Real Madrid"},
    {"id_jugador": 2, "nombre": "Lionel", "apellido": "Messi", "goles": 8, "club": "Inter Miami"}
  ]
}
```

Si la tabla conectada no tiene esa columna, estas rutas responden HTTP 200 con `{"disponible": false, "mensaje": "La tabla jugadores no contiene la columna goles; no se calcularon estadísticas de goles."}`. Las consultas no convierten valores `NULL` en cero. La definición de la columna usa `NOT NULL DEFAULT 0`, por lo que al agregarla a una tabla existente MySQL inicializa los registros previos con cero.

### Acceso MySQL y Tools de Gemini

Las consultas filtran texto con parámetros `%s`; únicamente se ensamblan fragmentos SQL constantes para las categorías de posición. Las relaciones se resuelven con `JOIN jugadores.id_club = clubes.id_club`; las agrupaciones y promedios se calculan en MySQL y las listas quedan limitadas a 100. Las funciones `buscar_jugadores_por_campos`, `obtener_jugador_detallado`, `consultar_jugadores_por_categoria`, `consultar_categoria_por_club`, `consultar_categoria_por_seleccion`, `consultar_goles_por_jugador`, `consultar_maximo_goleador`, `consultar_promedio_goles`, `consultar_goles_agrupados`, `comparar_goles_jugadores` y `consultar_estadisticas_por_posicion` están agregadas a `HERRAMIENTAS_GEMINI` en `routers/chat_tools.py`. `routers/chat.py` entrega esa lista a `GenerateContentConfig(tools=...)`; para añadir otra Tool, agrega una función de consulta con type hints y docstring y luego inclúyela en esa lista. Gemini debe tratar `disponible: false` como falta de columna y no deducir cifras.

Preguntas para probar en `POST /api/chat` desde Swagger:

- `¿Quiénes son todos los defensas de la selección de España?`
- `¿Qué mediocampistas pertenecen al Barcelona?`
- `¿Quién es el jugador con más goles?`
- `¿Cuántos goles tienen los defensas?`
- `¿Qué mediocampista tiene más goles?`
- `Compara los goles de Lionel Messi, Kylian Mbappé y Harry Kane.`
- `¿Cuántos goles han marcado los jugadores de cada selección?`
- `Busca los jugadores de apellido Martínez que sean defensas.`
