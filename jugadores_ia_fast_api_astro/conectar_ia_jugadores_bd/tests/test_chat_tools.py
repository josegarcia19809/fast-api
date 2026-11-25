"""Pruebas unitarias sin requerir una instancia MySQL ni una clave Gemini."""
import unittest
import sys
import types
from unittest.mock import patch

# El entorno de pruebas local puede no tener instaladas las dependencias de MySQL.
# La capa de consultas se parchea en cada test; este stub solo permite importarla.
try:
    import mysql.connector  # noqa: F401
except ModuleNotFoundError:
    mysql_module = types.ModuleType("mysql")
    connector_module = types.ModuleType("mysql.connector")
    connector_module.Error = Exception
    connector_module.connect = lambda **kwargs: None
    mysql_module.connector = connector_module
    sys.modules["mysql"] = mysql_module
    sys.modules["mysql.connector"] = connector_module

from routers import chat_tools as tools


class HerramientasChatTests(unittest.TestCase):
    def test_registro_contiene_las_33_herramientas_requeridas(self):
        nombres = {herramienta.__name__ for herramienta in tools.HERRAMIENTAS_GEMINI}
        esperadas = {
            "consultar_jugadores", "buscar_jugador", "consultar_jugadores_por_edad",
            "consultar_jugadores_por_numero", "consultar_jugadores_ordenados",
            "consultar_por_nacionalidad", "consultar_nacionalidades", "consultar_por_posicion",
            "consultar_cantidad_por_posicion", "consultar_promedio_edad_por_posicion",
            "consultar_jugador_mas_alto", "consultar_jugador_mas_bajo",
            "consultar_jugador_mas_pesado", "consultar_promedios_fisicos",
            "consultar_por_pie_dominante", "consultar_jugador_mas_valioso",
            "consultar_jugador_menos_valioso", "consultar_valor_total_mercado",
            "consultar_promedio_valor_mercado", "consultar_jugadores_por_valor",
            "consultar_valor_mercado_por_nacionalidad", "consultar_clubes", "buscar_club",
            "consultar_clubes_por_pais", "consultar_clubes_por_liga",
            "consultar_jugadores_por_club", "consultar_cantidad_jugadores_por_club",
            "consultar_jugadores_por_liga", "consultar_valor_mercado_por_liga",
            "consultar_estadisticas_por_club", "consultar_jugadores_por_pais_club",
            "comparar_clubes", "consultar_jugadores_por_antiguedad_club",
        }
        self.assertTrue(esperadas.issubset(nombres))

    @patch.object(tools, "consultar_uno", return_value=None)
    @patch.object(tools, "consultar_todos", return_value=[])
    def test_herramientas_disparan_consultas_mysql_controladas(self, consultar_todos, consultar_uno):
        invocaciones = {
            "consultar_jugadores": (), "buscar_jugador": ("Ada",),
            "consultar_jugadores_por_edad": (18, 30),
            "consultar_jugadores_por_numero": (7,),
            "consultar_jugadores_ordenados": ("edad",),
            "consultar_por_nacionalidad": ("francesa",),
            "consultar_nacionalidades": (), "consultar_por_posicion": ("medio",),
            "consultar_cantidad_por_posicion": (),
            "consultar_promedio_edad_por_posicion": (),
            "consultar_jugador_mas_alto": (), "consultar_jugador_mas_bajo": (),
            "consultar_jugador_mas_pesado": (), "consultar_promedios_fisicos": (),
            "consultar_por_pie_dominante": ("zurdo",),
            "consultar_jugador_mas_valioso": (), "consultar_jugador_menos_valioso": (),
            "consultar_valor_total_mercado": (), "consultar_promedio_valor_mercado": (),
            "consultar_jugadores_por_valor": (1, 200),
            "consultar_valor_mercado_por_nacionalidad": (),
            "consultar_clubes": (), "buscar_club": ("Madrid",),
            "consultar_clubes_por_pais": ("España",),
            "consultar_clubes_por_liga": ("Premier",),
            "consultar_jugadores_por_club": ("Madrid",),
            "consultar_cantidad_jugadores_por_club": (),
            "consultar_jugadores_por_liga": ("Premier",),
            "consultar_valor_mercado_por_liga": (),
            "consultar_estadisticas_por_club": (),
            "consultar_jugadores_por_pais_club": ("España",),
            "comparar_clubes": ("Real Madrid", "Manchester City"),
            "consultar_jugadores_por_antiguedad_club": (1900,),
            "obtener_imagen_jugador": ("Ada",),
            "consultar_estadisticas_jugadores": (),
            "obtener_informacion_club": ("Real Madrid",),
            "comparar_jugadores": ("Jugador Uno", "Jugador Dos"),
        }
        mapa = {herramienta.__name__: herramienta for herramienta in tools.HERRAMIENTAS_GEMINI}
        for nombre, argumentos in invocaciones.items():
            with self.subTest(herramienta=nombre):
                consultar_todos.reset_mock()
                consultar_uno.reset_mock()
                mapa[nombre](*argumentos)
                self.assertTrue(consultar_todos.called or consultar_uno.called)

    @patch.object(tools, "consultar_todos", return_value=[])
    def test_busqueda_parametriza_nombre_y_limita_resultados(self, consultar):
        self.assertEqual(tools.buscar_jugador("Ada"), [])
        sql, parametros = consultar.call_args.args
        self.assertIn("j.nombre LIKE %s", sql)
        self.assertIn("JOIN clubes", sql)
        self.assertEqual(parametros, ("%Ada%", "%Ada%", "%Ada%", tools.LIMITE_RESULTADOS))

    @patch.object(tools, "consultar_todos", return_value=[])
    def test_filtros_validan_rangos_y_usan_parametros(self, consultar):
        tools.consultar_jugadores_por_edad(18, 25)
        self.assertEqual(consultar.call_args.args[1], (18, 25, tools.LIMITE_RESULTADOS))
        with self.assertRaises(ValueError):
            tools.consultar_jugadores_por_edad(30, 20)
        with self.assertRaises(ValueError):
            tools.consultar_jugadores_por_valor(500, 100)

    @patch.object(tools, "consultar_todos", return_value=[])
    def test_ordenamiento_no_acepta_sql_como_criterio(self, consultar):
        respuesta = tools.consultar_jugadores_ordenados("edad; DROP TABLE jugadores")
        self.assertIn("error", respuesta)
        consultar.assert_not_called()

    @patch.object(tools, "consultar_todos", return_value=[])
    def test_consultas_combinadas_usan_join_group_by_y_valores_parametrizados(self, consultar):
        tools.comparar_clubes("Club A", "Club B")
        sql, parametros = consultar.call_args.args
        self.assertIn("LEFT JOIN jugadores", sql)
        self.assertIn("GROUP BY", sql)
        self.assertIn("LOWER(%s)", sql)
        self.assertEqual(parametros, ("Club A", "Club B", tools.LIMITE_RESULTADOS))

    @patch.object(tools, "consultar_uno", return_value=None)
    def test_extremo_sin_registros_devuelve_none_estructurado(self, consultar):
        resultado = tools.consultar_jugador_mas_alto()
        self.assertEqual(resultado, {"mas_alto": None})
        self.assertIn("ORDER BY j.altura DESC", consultar.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
