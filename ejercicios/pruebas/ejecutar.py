"""Pruebas demostrables del DSL. Uso: python ejercicios/pruebas/ejecutar.py."""
import argparse
import contextlib
import csv
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parents[1]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "generado")]

from datos.lista import Lista
from datos.lector_csv import LectorCSV
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import es_nada
from errores_base import ErrorArepa
from lenguaje.analizador import analizar
from runtime.ejecutor import EjecutorArepa


def normalizar(valor):
    if es_nada(valor):
        return None
    if isinstance(valor, Tabla):
        return {"columnas": valor.nombres_columnas,
                "filas": [[normalizar(v) for v in f.valores] for f in valor.filas]}
    if isinstance(valor, Lista):
        return [normalizar(v) for v in valor]
    if isinstance(valor, Registro):
        return dict(zip(valor.claves(), map(normalizar, valor.valores())))
    if isinstance(valor, float) and math.isinf(valor):
        return "infinito" if valor > 0 else "-infinito"
    return valor


class Ejemplos(unittest.TestCase):
    def setUp(self):
        self.anterior = Path.cwd()
        self.temporal = tempfile.TemporaryDirectory(prefix="arepa_pruebas_")
        self.trabajo = Path(self.temporal.name)
        # Cada prueba comienza con datos y salidas limpios: nunca acepta archivos viejos.
        for nombre in ("datos", "ejercicios/datos", "ejercicios/pruebas/datos",
                       "caso_estudio/datos", "pruebas/datos"):
            shutil.copytree(RAIZ / nombre, self.trabajo / nombre,
                            ignore=shutil.ignore_patterns("salidas", "__pycache__"))
        (self.trabajo / "salidas").mkdir()
        os.chdir(self.trabajo)
        self.env_anterior = os.environ.get("AREPA_SIN_VENTANA")
        os.environ["AREPA_SIN_VENTANA"] = "1"

    def tearDown(self):
        os.chdir(self.anterior)
        if self.env_anterior is None:
            os.environ.pop("AREPA_SIN_VENTANA", None)
        else:
            os.environ["AREPA_SIN_VENTANA"] = self.env_anterior
        self.temporal.cleanup()

    def comparar(self, obtenido, esperado):
        if isinstance(esperado, dict):
            self.assertIsInstance(obtenido, dict)
            self.assertEqual(set(obtenido), set(esperado))
            for clave, valor in esperado.items():
                with self.subTest(campo=clave):
                    self.comparar(obtenido[clave], valor)
        elif isinstance(esperado, list):
            self.assertIsInstance(obtenido, list)
            self.assertEqual(len(obtenido), len(esperado))
            for i, (a, b) in enumerate(zip(obtenido, esperado)):
                with self.subTest(indice=i):
                    self.comparar(a, b)
        elif isinstance(esperado, (int, float)) and not isinstance(esperado, bool):
            self.assertIsInstance(obtenido, (int, float))
            self.assertNotIsInstance(obtenido, bool)
            self.assertTrue(math.isclose(obtenido, esperado, rel_tol=1e-7, abs_tol=1e-7),
                            f"{obtenido!r} != {esperado!r}")
        else:
            self.assertEqual(type(obtenido), type(esperado))
            self.assertEqual(obtenido, esperado)

    def programa(self, ruta):
        texto = (RAIZ / ruta).read_text(encoding="utf-8-sig")
        _, arbol, errores = analizar(texto)
        self.assertFalse(errores, str(errores))
        ejecutor = EjecutorArepa()
        with contextlib.redirect_stdout(io.StringIO()):
            ejecutor.ejecutar(arbol)
        return ejecutor

    def png(self, ruta):
        datos = Path(ruta).read_bytes()
        self.assertEqual(datos[:8], b"\x89PNG\r\n\x1a\n")
        pos, bloques, comprimido = 8, [], bytearray()
        while pos < len(datos):
            self.assertGreaterEqual(len(datos) - pos, 12)
            largo = struct.unpack_from(">I", datos, pos)[0]
            tipo = datos[pos + 4:pos + 8]
            fin = pos + 8 + largo
            self.assertLessEqual(fin + 4, len(datos))
            contenido = datos[pos + 8:fin]
            crc = struct.unpack_from(">I", datos, fin)[0]
            self.assertEqual(crc, zlib.crc32(tipo + contenido) & 0xffffffff)
            bloques.append(tipo)
            if tipo == b"IHDR":
                self.assertEqual(struct.unpack(">IIBBBBB", contenido),
                                 (800, 480, 8, 2, 0, 0, 0))
            if tipo == b"IDAT":
                comprimido.extend(contenido)
            if tipo == b"IEND":
                self.assertEqual(largo, 0)
            pos = fin + 4
        self.assertEqual(bloques[0], b"IHDR")
        self.assertEqual(bloques.count(b"IHDR"), 1)
        self.assertEqual(bloques[-1], b"IEND")
        self.assertEqual(bloques.count(b"IEND"), 1)
        self.assertIn(b"IDAT", bloques)
        pixeles = zlib.decompress(comprimido)
        self.assertEqual(len(pixeles), 480 * (1 + 800 * 3))
        # El codificador propio usa scanlines sin filtro; exigir dibujo no uniforme.
        colores = set()
        for y in range(480):
            inicio = y * 2401
            self.assertEqual(pixeles[inicio], 0)
            fila = pixeles[inicio + 1:inicio + 2401]
            colores.update(fila[x:x + 3] for x in range(0, 2400, 3))
        self.assertGreater(len(colores), 3, "PNG vacío o sin contenido gráfico")
        return datos

    def positivo(self, caso):
        ruta_programa = (caso["archivo"] if caso.get("desde_raiz")
                         else "ejercicios/pruebas/" + caso["archivo"])
        ejecutor = self.programa(ruta_programa)
        self.assertFalse(ejecutor.contexto.errores)
        for nombre, esperado in caso.get("variables", {}).items():
            with self.subTest(variable=nombre):
                self.comparar(normalizar(ejecutor.contexto.simbolos.buscar(nombre)), esperado)
        if "salida" in caso:
            self.assertEqual(ejecutor.contexto.salida, caso["salida"])
        for fragmento in caso.get("contiene_salida", []):
            self.assertIn(fragmento, "\n".join(ejecutor.contexto.salida))
        registrados = {a["ruta"].replace("\\", "/") for a in ejecutor.contexto.archivos_generados}
        for ruta, filas in caso.get("csv", {}).items():
            with self.subTest(csv=ruta):
                self.assertIn(ruta, registrados)
                with open(ruta, encoding="utf-8", newline="") as archivo:
                    self.assertEqual(list(csv.reader(archivo)), filas)
        anteriores = {}
        for ruta in caso.get("png", []):
            with self.subTest(png=ruta):
                self.assertIn(ruta, registrados)
                anteriores[ruta] = self.png(ruta)
        if anteriores:
            # Volver a dibujar: mismo programa y datos deben producir los mismos bytes.
            self.programa(ruta_programa)
            for ruta, contenido in anteriores.items():
                self.assertEqual(Path(ruta).read_bytes(), contenido)

    def negativo(self, caso):
        ruta = RAIZ / "ejercicios/pruebas" / caso["archivo"]
        _, arbol, errores = analizar(ruta.read_text(encoding="utf-8-sig"))
        if caso["error"] == "sintaxis":
            self.assertTrue(errores, "Se aceptó un programa inválido")
            return
        self.assertFalse(errores, str(errores))
        with self.assertRaises(ErrorArepa) as capturado:
            with contextlib.redirect_stdout(io.StringIO()):
                EjecutorArepa().ejecutar(arbol)
        self.assertEqual(type(capturado.exception).__name__, caso["error"])
        self.assertIn(caso["mensaje"], str(capturado.exception))
        self.assertFalse(list((self.trabajo / "salidas").iterdir()),
                         "Un programa inválido produjo archivos")

    def test_cli_ejecucion_y_diagnostico(self):
        for archivo, opciones, valido in (
            ("positivos/01_potencias.arepa", ["--ejecutar"], True),
            ("positivos/01_potencias.arepa", ["--arbol"], True),
            ("negativos/01_variable.arepa", ["--ejecutar"], False),
            ("negativos/20_sin_chao.arepa", [], False),
        ):
            with self.subTest(archivo=archivo, opciones=opciones):
                proceso = subprocess.run(
                    [sys.executable, str(RAIZ / "src/cli/main.py"),
                     str(CARPETA / archivo), *opciones, "--sin-ventana"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=30)
                self.assertEqual(proceso.returncode == 0, valido, proceso.stdout + proceso.stderr)
                self.assertNotIn("Traceback", proceso.stdout + proceso.stderr)
                if opciones == ["--ejecutar"] and valido:
                    self.assertIn("512", proceso.stdout)
                if not valido:
                    self.assertRegex(proceso.stdout + proceso.stderr, r"[Ll][íi]nea")

    def test_csv_multilinea_y_diagnosticos(self):
        for separador in (",", ";"):
            for salto in ("\n", "\r\n"):
                with self.subTest(separador=separador, salto=repr(salto)):
                    contenido = (f"nombre{separador}nota{salto}"
                                 f'Ana{separador}"primera{salto}{salto}dijo ""hola"""{salto}'
                                 f'Luis{separador}a"b{salto}')
                    lector = LectorCSV(separador=separador)
                    tabla = lector.leer_texto(contenido)
                    self.assertEqual(tabla.filas[0].valores,
                                     ["Ana", f'primera{salto}{salto}dijo "hola"'])
                    self.assertEqual(tabla.filas[1].valores, ["Luis", 'a"b'])
                    with self.assertRaises(ErrorArepa) as error:
                        lector.leer_texto(contenido + f'X{separador}"sin cierre{salto}')
                    self.assertEqual(error.exception.linea_archivo, 6)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Verificación completa desde la raíz del proyecto: "
               "python ejercicios/pruebas/ejecutar.py --completo")
    parser.add_argument("--completo", action="store_true",
                        help="Incluye suites internas y regresión de ejercicios, ejemplos y caso de estudio")
    parser.add_argument("--ejercicios", action="store_true",
                        help="Comprueba los resultados esperados de los ejercicios ampliados")
    opciones = parser.parse_args()
    manifiesto = json.loads((CARPETA / "esperados.json").read_text(encoding="utf-8"))
    for grupo, metodo in (("positivos", "positivo"), ("negativos", "negativo")):
        for caso in manifiesto[grupo]:
            def prueba(self, caso=caso, metodo=metodo):
                getattr(self, metodo)(caso)
            nombre = Path(caso["archivo"]).stem
            setattr(Ejemplos, "test_" + grupo + "_" + nombre, prueba)
    verificados = set()
    if opciones.completo or opciones.ejercicios:
        catalogo = json.loads((RAIZ / "ejercicios/resultados_esperados.json").read_text(encoding="utf-8"))
        for caso in catalogo:
            def ejercicio(self, caso=caso):
                self.positivo(caso)
            nombre = caso["archivo"].removesuffix(".arepa").replace("/", "_")
            setattr(Ejemplos, "test_" + nombre, ejercicio)
            verificados.add(caso["archivo"])
    if opciones.completo:
        rutas = sorted((RAIZ / "ejercicios").glob("corte*/**/*.arepa"))
        rutas += sorted((RAIZ / "ejemplos").glob("*.arepa"))
        rutas += [RAIZ / "caso_estudio/programa.arepa"]
        rutas = [ruta for ruta in rutas if ruta.relative_to(RAIZ).as_posix() not in verificados]
        for i, ruta in enumerate(rutas):
            def regresion(self, ruta=ruta):
                self.programa(ruta.relative_to(RAIZ))
            setattr(Ejemplos, f"test_regresion_{i:03d}_{ruta.stem}", regresion)
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(Ejemplos),
        unittest.defaultTestLoader.discover(str(CARPETA), pattern="test_*.py"),
    ])
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    correcto = resultado.wasSuccessful()
    if opciones.completo:
        proceso = subprocess.run([sys.executable, str(RAIZ / "pruebas/test_proyecto.py")],
                                 cwd=RAIZ, timeout=300,
                                 env={**os.environ, "AREPA_SIN_VENTANA": "1"})
        correcto = correcto and proceso.returncode == 0
    return 0 if correcto else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
