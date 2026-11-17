"""Contratos de la consola: causas útiles, ubicación y ausencia de falsos errores."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "generado")]
from cli.main import _ejecutar
from lenguaje.analizador import analizar
from runtime.ejecutor import EjecutorArepa


class DiagnosticosConsola(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="arepa_diagnosticos_")
        self.carpeta = Path(self.temporal.name)
        self.addCleanup(self.temporal.cleanup)

    def cli(self, cuerpo, *opciones, envuelto=True):
        fuente = "quihubo\n" + cuerpo + "\nchao\n" if envuelto else cuerpo
        ruta = self.carpeta / "programa.arepa"
        ruta.write_text(fuente, encoding="utf-8")
        resultado = subprocess.run(
            [sys.executable, str(RAIZ / "src/cli/main.py"), str(ruta),
             *(opciones or ("--ejecutar",)), "--sin-ventana"],
            cwd=self.carpeta, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
            env={**os.environ, "AREPA_SIN_VENTANA": "1"})
        self.assertNotIn("Traceback", resultado.stdout + resultado.stderr)
        return resultado

    def error(self, cuerpo, clase, fragmento):
        r = self.cli(cuerpo)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for esperado in (clase, fragmento, "Causa:", "Cómo corregir:", "Archivo fuente:", "Línea"):
            self.assertIn(esperado, r.stdout)
        self.assertNotIn("corrió completo", r.stdout)
        return r.stdout

    def test_todos_los_negativos_tienen_diagnostico(self):
        carpeta = RAIZ / "ejercicios/pruebas"
        casos = json.loads((carpeta / "esperados.json").read_text(encoding="utf-8"))["negativos"]
        for caso in casos:
            with self.subTest(archivo=caso["archivo"]):
                r = subprocess.run(
                    [sys.executable, str(RAIZ / "src/cli/main.py"),
                     str(carpeta / caso["archivo"]), "--ejecutar", "--sin-ventana"],
                    cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("Cómo corregir:", r.stdout)
                self.assertIn("Línea", r.stdout)
                self.assertNotIn("Traceback", r.stdout + r.stderr)
                self.assertNotIn("corrió completo", r.stdout)

    def test_operador_marca_la_columna_exacta(self):
        s = self.error('x = 1 + "hola"', "ErrorTipos", "valor derecho")
        self.assertIn("Línea 2, Columna 6", s)
        lineas = s.splitlines()
        indice = next(i for i, l in enumerate(lineas) if "Línea 2: x =" in l)
        self.assertEqual(lineas[indice + 1].index("^"), lineas[indice].index("+"))

    def test_pipeline_marca_la_etapa_fallida(self):
        s = self.error('t = arme [x] con [[1]]\nr = t\n|> escoja [ausente]', "ErrorColumna", "ausente")
        self.assertIn("Línea 4, Columna", s)
        for cuerpo in (
            't = arme [x] con [[1]]\nr = t |> cree x = 2',
            't = arme [x, z] con [[1, 2]]\nr = t |> renombre x -> z',
        ):
            with self.subTest(cuerpo=cuerpo):
                s = self.error(cuerpo, "ErrorColumna", "ya existe")
                self.assertIn("nombre nuevo", s)

    def test_conversion_identifica_la_fila(self):
        s = self.error('t = arme [x] con [["1"], ["abc"]]\nr = t |> convierta x -> numero', "ErrorTipos", "abc")
        self.assertIn("fila 2", s)
        self.assertIn("Línea 3, Columna", s)

    def test_error_por_fila_conserva_valores(self):
        s = self.error('t = arme [x] con [["abc"]]\nr = t |> cree doble = x * 2', "ErrorTipos", "texto")
        self.assertIn("x='abc'", s)
        self.assertIn("valores de la fila", s)

    def test_funcion_conserva_origen_y_llamada(self):
        s = self.error('invente doble(n) {\n devuelva n * 2\n}\nr = doble("abc")', "ErrorTipos", "texto")
        self.assertIn("Línea 3, Columna", s)
        self.assertIn("Llamada a 'doble' desde Línea 5", s)

    def test_csv_distingue_fuente_y_linea_de_datos(self):
        (self.carpeta / "mal.csv").write_text('x,y\n1,"sin cerrar\n', encoding="utf-8")
        s = self.error('t = monte "mal.csv" con encabezado', "ErrorCSV", "Comillas sin cerrar")
        self.assertIn("Archivo de datos: mal.csv", s)
        self.assertIn("Línea del CSV: 2", s)
        self.assertIn("Línea 2, Columna", s)
        self.assertRegex(s, r"sin cerrar(?:\\r)?\\n")

    def test_guardar_csv_en_directorio_es_error_descrito(self):
        (self.carpeta / "destino.csv").mkdir()
        self.error('t = arme [x] con [[1]]\nguarde t como "destino.csv"', "ErrorArchivo", "No pude guardar")

    def test_fuente_no_utf8(self):
        ruta = self.carpeta / "invalido.arepa"
        ruta.write_bytes(b"quihubo\nx = '\xff'\nchao\n")
        r = subprocess.run([sys.executable, str(RAIZ / "src/cli/main.py"), str(ruta)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn("UTF-8", r.stdout)
        self.assertIn("Cómo corregir:", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_archivo_fuente_ausente(self):
        ruta = self.carpeta / "ausente.arepa"
        r = subprocess.run([sys.executable, str(RAIZ / "src/cli/main.py"), str(ruta)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn("ErrorArchivo", r.stdout)
        self.assertIn("Cómo corregir:", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_sintaxis_muestra_final_de_archivo(self):
        r = self.cli("quihubo\nx = 1\n", envuelto=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("(fin del archivo)", r.stdout)
        self.assertIn("Cómo corregir:", r.stdout)
        self.assertNotIn("Ejecución con", r.stdout)

    def test_cadena_abierta_explica_comillas(self):
        r = self.cli('quihubo\nx = "sin cerrar\nchao\n', envuelto=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Cerrá la cadena con comillas dobles", r.stdout)

    def test_divisiones_cero_avisan_y_no_interrumpen(self):
        r = self.cli('a = 1 / 0\nb = -1 / 0\nc = 0 / 0\nd = 5 % 0\ne = 0 ^ -1\ncuenteme a, b, c, d, e\ncuenteme "continúa"')
        self.assertEqual(r.returncode, 0, r.stdout)
        for fragmento in ("infinito -infinito nada nada infinito", "continúa",
                          "division_por_cero", "division_indefinida", "modulo_por_cero",
                          "potencia_cero_negativa", "no está definida", "Qué revisar:"):
            self.assertIn(fragmento, r.stdout)
        self.assertNotIn("Error ", r.stdout)
        self.assertNotIn("sin tropiezos", r.stdout)

    def test_validos_no_tienen_falsas_alarmas(self):
        casos = [
            'cuenteme 10 / 2, 5 % 2, 2 ^ -3, (-2) ^ 3',
            'fijese_si (falso) { x = 1 / 0 }\ncuenteme 1',
            'repita 0 veces { x = 1 / 0 }\ncuenteme 1',
            'invente sin_llamar() { devuelva 1 / 0 }\ncuenteme 1',
            'cuenteme "1 / 0"\n# x = 1 / 0',
            'cuenteme nada / 0, nada + 1, nada == nada',
            't = arme [x]\nr = t |> resuma n = cuente(), total = sume(x)\ncuenteme r',
            't = arme [x] con [[nada], [1]]\nr = t |> deje donde x > 0\ncuenteme r',
            'x = [1, 2]\ncuenteme x[1], x[2]',
            't = arme [fecha] con [["2024-02-29"]]\nr = t |> convierta fecha -> fecha',
            'cuenteme -0, 0 / 2, 0 % 2, 0 ^ 0',
        ]
        for cuerpo in casos:
            with self.subTest(cuerpo=cuerpo):
                r = self.cli(cuerpo)
                self.assertEqual(r.returncode, 0, r.stdout)
                self.assertNotIn("Avisos de ejecución", r.stdout)
                self.assertNotIn("Error ", r.stdout)
                self.assertIn("corrió completo", r.stdout)

    def test_validar_no_ejecuta_ni_avisa(self):
        r = self.cli("x = 1 / 0", "--arbol")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Avisos de ejecución", r.stdout)

    def test_avisos_repetidos_se_agrupan(self):
        r = self.cli("repita 5 veces { x = 1 / 0 }\ncuenteme x")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.count("[division_por_cero]"), 1)
        self.assertIn("5 veces", r.stdout)

    def test_aviso_tabla_incluye_fila(self):
        r = self.cli('t = arme [x, divisor] con [[1, 0], [2, 0]]\nr = t |> cree cociente = x / divisor')
        self.assertEqual(r.returncode, 0)
        self.assertIn("ejemplo de fila afectada", r.stdout)
        self.assertIn("divisor=0", r.stdout)
        self.assertIn("2 veces", r.stdout)

    def test_aviso_previo_no_oculta_error_posterior(self):
        r = self.cli('x = 1 / 0\nr = ausente\ncuenteme "NO DEBE APARECER"')
        self.assertEqual(r.returncode, 1)
        self.assertIn("[division_por_cero]", r.stdout)
        self.assertIn("[ErrorVariable]", r.stdout)
        self.assertNotIn("NO DEBE APARECER", r.stdout)

    def test_potencia_no_real_si_es_error(self):
        s = self.error("x = (-1) ^ 0.5", "ErrorOperacion", "no tiene resultado real")
        self.assertIn("números complejos", s)

    def test_comparacion_no_admitida_no_filtra_traceback(self):
        self.error("a = [1]\nb = [2]\nr = a < b", "ErrorTipos", "no admite")

    def test_desbordamiento_representable_avisa(self):
        r = self.cli("x = 10.0 ^ 400\ncuenteme x")
        self.assertEqual(r.returncode, 0)
        self.assertIn("[desbordamiento_numerico]", r.stdout)

    def test_avisos_no_alteran_la_salida_del_programa(self):
        _, arbol, errores = analizar("quihubo\nx = 1 / 0\ncuenteme x\nchao\n")
        self.assertFalse(errores)
        e = EjecutorArepa()
        with contextlib.redirect_stdout(io.StringIO()):
            e.ejecutar(arbol)
        self.assertEqual(e.contexto.salida, ["infinito"])
        self.assertFalse(e.contexto.errores)
        self.assertEqual(len(e.contexto.advertencias), 1)

    def test_fallo_interno_se_identifica_como_interno(self):
        _, arbol, _ = analizar("quihubo\nx = 1\nchao\n")
        salida = io.StringIO()
        with patch.object(EjecutorArepa, "ejecutar", side_effect=RuntimeError("fallo simulado")):
            with contextlib.redirect_stdout(salida):
                codigo = _ejecutar(arbol, "quihubo\nx = 1\nchao\n", "programa.arepa")
        self.assertEqual(codigo, 1)
        self.assertIn("Error interno de ejecución", salida.getvalue())
        self.assertIn("no confirma", salida.getvalue())
        self.assertNotIn("Traceback", salida.getvalue())

    def test_repl_validar_incluye_ayuda(self):
        r = subprocess.run([sys.executable, str(RAIZ / "src/cli/repl.py"), "--simple"],
                           input="x = 1 @ 2\n:validar\n:salir\n", cwd=self.carpeta,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Cómo corregir:", r.stdout)
        self.assertIn("^", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_repl_guardar_invalido_no_cierra_consola(self):
        (self.carpeta / "destino.arepa").mkdir()
        r = subprocess.run([sys.executable, str(RAIZ / "src/cli/repl.py"), "--simple"],
                           input="x = 1\n:guardar destino.arepa\n:ver\n:salir\n", cwd=self.carpeta,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Cómo corregir:", r.stdout)
        self.assertIn("x = 1", r.stdout)
        self.assertIn("Chao.", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_argumentos_invalidos_tienen_causa_y_solucion(self):
        for argumentos in ([], ["--desconocido"], ["uno.arepa", "dos.arepa"]):
            with self.subTest(argumentos=argumentos):
                r = subprocess.run([sys.executable, str(RAIZ / "src/cli/main.py"), *argumentos],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                self.assertEqual(r.returncode, 2)
                self.assertIn("error:", r.stderr)
                self.assertIn("Cómo corregir:", r.stderr)
                self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_avisos_no_confunden_infinito_positivo_y_negativo(self):
        r = self.cli('t = arme [x, divisor] con [[-1, 0], [1, 0]]\nr = t |> cree cociente = x / divisor')
        self.assertEqual(r.returncode, 0)
        self.assertIn("resultado es -infinito", r.stdout)
        self.assertIn("resultado es infinito", r.stdout)
        self.assertEqual(r.stdout.count("[division_por_cero]"), 2)

    def test_recursion_profunda_se_explica(self):
        s = self.error("invente repetir() { devuelva repetir() }\nr = repetir()", "ErrorEjecucion", "recursión")
        self.assertIn("caso base", s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
