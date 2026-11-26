# Consultas del asistente de jugadores y clubes

## Esquema utilizado

`clubes`: `id_club` (PK), `nombre`, `pais`, `liga`, `estadio`, `anio_fundacion`.

`jugadores`: `id_jugador` (PK), `nombre`, `apellido`, `edad`, `nacionalidad`, `posicion`, `numero_camiseta`, `valor_mercado`, `altura`, `peso`, `pie_dominante`, `imagen`, `id_club`.

`jugadores.id_club` es una FK a `clubes.id_club`: cada jugador pertenece a un club y un club puede tener varios jugadores. Las herramientas usan exclusivamente estos campos y hacen `JOIN` cuando necesitan datos de ambas tablas. No se cambió el esquema.

## 30 preguntas sugeridas

### A. Consultas generales de jugadores

1. ¿Qué jugadores están registrados?
2. ¿Qué jugadores se llaman [nombre]?
3. ¿Qué información tienes de [nombre y apellido]?
4. ¿Qué jugadores tienen nacionalidad [nacionalidad]?
5. ¿Qué jugadores juegan como [posición]?
6. ¿Qué jugadores son zurdos, diestros o ambidiestros?

### B. Consultas estadísticas

7. ¿Cuántos jugadores hay registrados?
8. ¿Cuál es la edad promedio de los jugadores?
9. ¿Quién es el jugador más joven?
10. ¿Quién es el jugador de mayor edad?
11. ¿Cuál es la altura promedio?
12. ¿Quién es el jugador más alto y quién es el más bajo?
13. ¿Cuál es el valor de mercado promedio?
14. ¿Quién tiene el mayor y el menor valor de mercado?

### C. Consultas por clubes

15. ¿Qué clubes están registrados?
16. ¿Qué clubes hay en [país]?
17. ¿Qué clubes juegan en [liga]?
18. ¿Qué información hay del club [club]?
19. ¿Qué clubes tienen más jugadores registrados?
20. ¿Cuántos jugadores tiene cada club?
21. ¿Qué jugadores pertenecen al club [club]?
22. ¿Cuántos jugadores tiene el club [club]?

### D. Consultas combinadas

23. Compara a [jugador 1] y [jugador 2], que juegan en distintos clubes.
24. ¿Qué club tiene mayor edad promedio: [club 1] o [club 2]?
25. Compara los valores de mercado de los jugadores de [club 1] y [club 2].
26. ¿Qué nacionalidades están representadas en cada club?
27. ¿Qué [posición] juegan en el club [club]?
28. ¿Qué club tiene el mayor valor de mercado acumulado en su plantilla?
29. ¿Cuál es el valor de mercado total de cada club?
30. ¿Qué clubes tienen jugadores de nacionalidad [nacionalidad]?

## Herramientas, SQL y cálculo

Las funciones registradas como herramientas en `routers/chat.py` contienen el SQL parametrizado ejecutado por MySQL. En síntesis, las operaciones se basan en estos patrones (los nombres de columnas son los del esquema):

```sql
-- Listar/buscar jugadores; las variantes agregan filtros parametrizados
SELECT j.id_jugador, j.nombre, j.apellido, j.edad, j.nacionalidad,
       j.posicion, j.numero_camiseta, j.valor_mercado, j.altura,
       j.peso, j.pie_dominante, c.nombre AS club
FROM jugadores j JOIN clubes c ON c.id_club = j.id_club
WHERE j.nombre LIKE %s OR j.apellido LIKE %s
ORDER BY j.apellido, j.nombre;

-- Resumen global y extremos
SELECT COUNT(*) AS total_jugadores, AVG(edad) AS edad_promedio,
       AVG(altura) AS altura_promedio,
       AVG(valor_mercado) AS valor_mercado_promedio
FROM jugadores;
SELECT id_jugador, nombre, apellido, edad, altura, valor_mercado
FROM jugadores WHERE edad IS NOT NULL ORDER BY edad ASC, id_jugador LIMIT 1;
-- La herramienta repite el patrón de extremo para edad DESC, altura ASC/DESC
-- y valor_mercado ASC/DESC, excluyendo valores NULL.

-- Clubes, conteo, edad media, suma y nacionalidades por club
SELECT c.id_club, c.nombre, COUNT(j.id_jugador) AS cantidad_jugadores,
       AVG(j.edad) AS edad_promedio, SUM(j.valor_mercado) AS valor_mercado_total,
       GROUP_CONCAT(DISTINCT j.nacionalidad ORDER BY j.nacionalidad) AS nacionalidades
FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
GROUP BY c.id_club, c.nombre
ORDER BY cantidad_jugadores DESC, c.nombre;

-- Comparar clubes / ordenar ranking de valor de plantilla
SELECT c.nombre, COUNT(j.id_jugador) AS cantidad_jugadores,
       AVG(j.edad) AS edad_promedio, SUM(j.valor_mercado) AS valor_mercado_total,
       AVG(j.valor_mercado) AS valor_mercado_promedio
FROM clubes c LEFT JOIN jugadores j ON j.id_club = c.id_club
WHERE LOWER(c.nombre) IN (LOWER(%s), LOWER(%s))
GROUP BY c.id_club, c.nombre ORDER BY c.nombre;
```

Los filtros de club, posición, pie, nacionalidad y liga también usan parámetros `%s`; las herramientas de agregación calculan conteos y estadísticas en MySQL, en lugar de traer plantillas completas para procesarlas en Python. El prompt de sistema indica a Gemini que debe basarse en resultados de herramientas, declarar cuando no haya resultados y responder en español de México.

## Ejemplos para probar en `POST /api/chat`

- `¿Quiénes son los jugadores argentinos que juegan como delantero?`
- `¿Cuál es la edad promedio y quién es el más joven?`
- `¿Qué clubes juegan en La Liga y cuántos jugadores tiene cada uno?`
- `Compara la edad promedio y el valor de mercado total de [club 1] y [club 2].`
- `¿Qué jugadores de [posición] pertenecen a [club]?`
- `Ordena los clubes por valor de mercado acumulado.`
- `Muéstrame la foto de [nombre del jugador].`

Sustituye los valores entre corchetes por nombres que existan en la base de datos. Si una búsqueda no devuelve filas, Gemini debe indicarlo sin completar la respuesta con datos externos.

Para solicitudes de imágenes, Gemini utiliza `obtener_imagen_jugador(nombre)`, que devuelve el campo `jugadores.imagen` junto con el jugador y su club. Cuando ese valor sea una URL pública, la instrucción del sistema pide presentarlo como imagen Markdown. Si el campo es `NULL` o está vacío, debe indicarse que el jugador no tiene imagen registrada. Una ruta local no será visible para el cliente hasta que el archivo esté servido por una URL accesible.
