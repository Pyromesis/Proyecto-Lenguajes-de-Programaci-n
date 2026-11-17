"""Regresiones adversariales de datos, modelos y límites numéricos."""
import contextlib
import csv
import io
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "generado")]
from datos.escritor_csv import EscritorCSV
from datos.lector_csv import LectorCSV
from datos.tabla import Tabla
from datos.tipos import NADA, formatear_numero
from errores_base import ErrorColumna, ErrorCSV, ErrorSemantico
from lenguaje.analizador import analizar
from ml import metricas
from ml.modelo import exigir_numero_positivo
from ml.preprocesamiento import Preprocesador
from ml.regresion_lineal import RegresionLineal
from runtime.ejecutor import EjecutorArepa


class Auditoria(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="arepa_auditoria_")
        self.carpeta = Path(self.temporal.name)
        self.addCleanup(self.temporal.cleanup)

    def cli(self, cuerpo):
        ruta = self.carpeta / "caso.arepa"
        ruta.write_text("quihubo\n" + cuerpo + "\nchao\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(RAIZ / "src/cli/main.py"),
                            str(ruta), "--ejecutar", "--sin-ventana"], cwd=self.carpeta,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        self.assertNotIn("Error interno", r.stdout + r.stderr)
        return r

    def ida_vuelta(self, filas, columnas=("valor",), separador=","):
        tabla = Tabla.desde_filas(columnas, filas)
        ruta = self.carpeta / "datos.csv"
        EscritorCSV(separador).escribir(ruta, tabla)
        nueva = LectorCSV(separador).leer(ruta)
        self.assertEqual(nueva.nombres_columnas, list(columnas))
        self.assertEqual([f.valores for f in nueva.filas], filas)
        return nueva

    def test_no_admite_columnas_duplicadas(self):
        with self.assertRaises(ErrorColumna):
            Tabla.desde_filas(["x", "x"], [[1, 2]])
        r = self.cli('t = arme [x, x] con [[1, 2]]')
        self.assertEqual(r.returncode, 1)
        self.assertIn("repetido", r.stdout)
        self.assertIn("Cómo corregir", r.stdout)

    def test_csv_rechaza_encabezado_ambiguo(self):
        for contenido in ("x,x\n1,2\n", ",columna_1\n1,2\n"):
            with self.subTest(contenido=contenido):
                with self.assertRaises(ErrorCSV) as error:
                    LectorCSV().leer_texto(contenido)
                self.assertEqual(error.exception.linea_archivo, 1)

    def test_seleccion_no_crea_columnas_duplicadas(self):
        tabla = Tabla.desde_filas(["x"], [[1]])
        with self.assertRaises(ErrorColumna):
            tabla.seleccionar(["x", "x"])

    def test_csv_preserva_espacios_y_filas_vacias_de_texto(self):
        self.ida_vuelta([[" Ana "], ["   "], [""], ["\t"], ["\n"]])

    def test_csv_preserva_textos_que_parecen_otros_tipos(self):
        nueva = self.ida_vuelta([["001"], ["1.0"], ["obvio"], ["falso"], ["nada"], ["infinito"], ["-2"]])
        self.assertTrue(all(isinstance(f.valores[0], str) for f in nueva.filas))

    def test_csv_no_pierde_filas_con_solo_nada(self):
        self.ida_vuelta([[NADA], [""], [NADA], ["nada"]])

    def test_csv_lectura_citada_es_texto_explicito(self):
        tabla = LectorCSV().leer_texto('x,y\n"001",1\n"obvio",obvio\n"",\n"nada",nada\n')
        self.assertEqual([f.valores for f in tabla.filas],
                         [["001", 1], ["obvio", True], ["", NADA], ["nada", NADA]])

    def test_csv_muchos_datos_conservan_valores_y_tipos(self):
        aleatorio = random.Random(108)
        opciones = [NADA, "", " a ", "001", 'dijo "hola"', "a,b", "a;b", "línea\notra", "obvio", True, False, -3, 2.25]
        filas = [[aleatorio.choice(opciones) for _ in range(4)] for _ in range(100)]
        for separador in (",", ";", "|"):
            with self.subTest(separador=separador):
                nueva = self.ida_vuelta(filas, ("a", "b", "c", "d"), separador)
                for original, obtenida in zip(filas, nueva.filas):
                    self.assertEqual([type(v) for v in original], [type(v) for v in obtenida.valores])

    def test_csv_estandar_puede_leer_la_exportacion(self):
        filas = [[" a ", "001"], ["", 'dijo "hola"']]
        self.ida_vuelta(filas, ("nombre", "codigo"))
        with open(self.carpeta / "datos.csv", encoding="utf-8", newline="") as archivo:
            self.assertEqual(list(csv.reader(archivo)), [["nombre", "codigo"], *filas])

    def test_csv_no_acepta_texto_despues_de_comillas(self):
        with self.assertRaises(ErrorCSV):
            LectorCSV().leer_texto('x\n"Ana"basura\n')

    def test_tasa_debe_ser_finita(self):
        for tasa in (float("inf"), float("-inf"), float("nan"), 0, -1, True):
            with self.subTest(tasa=tasa):
                with self.assertRaises(ErrorSemantico):
                    exigir_numero_positivo(tasa, "tasa")

    def test_tasa_infinita_no_anuncia_entrenamiento(self):
        r = self.cli('t = arme [x, respuesta] con [[1, 2], [2, 4], [3, 6]]\n'
                     'entrene m = regresion con t\ncolumnas [x]\nobjetivo respuesta\ntasa 1 / 0\nepocas 5')
        self.assertEqual(r.returncode, 1)
        self.assertIn("finito", r.stdout)
        self.assertNotIn("[entrene]", r.stdout)
        self.assertNotIn("corrió completo", r.stdout)

    def test_divergencia_no_produce_nan_ni_exito(self):
        r = self.cli('t = arme [x, respuesta] con [[1, 2], [2, 4], [3, 6]]\n'
                     'entrene m = regresion con t\ncolumnas [x]\nobjetivo respuesta\ntasa 100\nepocas 200\n'
                     'r = t |> prediga con m como estimado\nevalua m con t')
        self.assertEqual(r.returncode, 1)
        self.assertIn("diverg", r.stdout)
        self.assertNotIn("[entrene]", r.stdout)
        self.assertNotIn("MAE  = nan", r.stdout)
        self.assertNotIn("corrió completo", r.stdout)

    def test_modelo_fallido_no_queda_entrenado(self):
        t = Tabla.desde_filas(["x", "respuesta"], [[1, 2], [2, 4], [3, 6]])
        pre = Preprocesador(t, ["x"], "respuesta")
        X, y = pre.datos(t, estandarizar=True)
        modelo = RegresionLineal(pre, "respuesta", tasa=100, epocas=200)
        with self.assertRaises(ErrorSemantico):
            modelo.entrenar(X, y)
        self.assertFalse(modelo.entrenado)
        with self.assertRaises(ErrorSemantico):
            modelo.predecir([0])

    def test_pocas_epocas_no_son_un_error(self):
        r = self.cli('t = arme [x, respuesta] con [[1, 2], [2, 4], [3, 6]]\n'
                     'entrene m = regresion con t\ncolumnas [x]\nobjetivo respuesta\ntasa 0.01\nepocas 1\nevalua m con t')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("[entrene]", r.stdout)
        self.assertNotIn("nan", r.stdout.lower())

    def test_objetivo_constante_valido_con_tasa_grande(self):
        r = self.cli('t = arme [x, respuesta] con [[1, 5], [2, 5], [3, 5]]\n'
                     'entrene m = regresion con t\ncolumnas [x]\nobjetivo respuesta\ntasa 100\nepocas 20\nevalua m con t')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("R²   = 1", r.stdout)

    def test_preprocesamiento_no_desborda_escala_valida(self):
        for escala in (1e200, 1e-200):
            with self.subTest(escala=escala):
                t = Tabla.desde_filas(["x", "respuesta"], [[-escala, 1], [escala, 2]])
                pre = Preprocesador(t, ["x"], "respuesta")
                X, _ = pre.datos(t, estandarizar=True)
                self.assertAlmostEqual(X[0][0], -1)
                self.assertAlmostEqual(X[1][0], 1)

    def test_entrada_no_finita_se_rechaza(self):
        t = Tabla.desde_filas(["x", "respuesta"], [[float("inf"), 1], [2, 2]])
        with self.assertRaises(ErrorSemantico):
            Preprocesador(t, ["x"], "respuesta")

    def test_metricas_no_aceptan_predicciones_no_finitas(self):
        for funcion in (metricas.error_absoluto_medio, metricas.error_cuadratico_medio,
                        metricas.raiz_error_cuadratico, metricas.coeficiente_determinacion):
            for valor in (float("nan"), float("inf")):
                with self.subTest(funcion=funcion.__name__, valor=valor):
                    with self.assertRaises(ErrorSemantico):
                        funcion([1, 2], [valor, 2])

    def test_metricas_validas_con_magnitudes_grandes(self):
        self.assertEqual(metricas.coeficiente_determinacion([1e200, 2e200], [1e200, 2e200]), 1)
        self.assertAlmostEqual(metricas.raiz_error_cuadratico([1e200], [0]) / 1e200, 1)
        self.assertAlmostEqual(metricas.error_absoluto_medio([1e308] + [0] * 9,
                                                         [-1e308] + [0] * 9) / 1e307, 2)
        with self.assertRaises(ErrorSemantico):
            metricas.error_cuadratico_medio([1e200], [0])

    def test_potencia_de_5001_digitos_se_muestra(self):
        r = self.cli("x = 10 ^ 5000\ncuenteme x")
        self.assertEqual(r.returncode, 0, r.stdout[-500:])
        self.assertIn("\n" + "1" + "0" * 5000 + "\n", r.stdout)

    def test_literal_largo_se_lee_sin_cambiar_limites_python(self):
        limite = sys.get_int_max_str_digits()
        numero = "9" * 5000
        r = self.cli("x = " + numero + "\ncuenteme x")
        self.assertEqual(r.returncode, 0, r.stdout[-500:])
        self.assertIn("\n" + numero + "\n", r.stdout)
        self.assertEqual(sys.get_int_max_str_digits(), limite)

    def test_entero_largo_se_conserva_en_csv(self):
        numero = 10 ** 5000
        self.ida_vuelta([[numero], [-numero]])
        self.assertEqual(formatear_numero(numero), "1" + "0" * 5000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
