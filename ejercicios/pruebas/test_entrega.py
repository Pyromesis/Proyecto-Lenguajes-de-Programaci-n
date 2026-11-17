"""Integridad y reproducibilidad del paquete que se entrega al docente."""
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from herramientas.crear_entrega import crear_paquete, verificar_paquete


class Entrega(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="arepa_paquete_")
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def test_incluye_fuentes_nuevas_datos_y_pruebas(self):
        ruta = self.carpeta / "entrega.zip"
        crear_paquete(ruta)
        self.assertGreater(verificar_paquete(ruta), 400)
        with zipfile.ZipFile(ruta) as archivo:
            nombres = archivo.namelist()
            for requerido in ("src/runtime/ejecucion_modelos.py", "src/utiles/enteros.py",
                              "ejercicios/pruebas/test_auditoria.py", "caso_estudio/datos/pasajeros.csv",
                              ".github/workflows/verificacion.yml"):
                self.assertIn(requerido, nombres)
            self.assertFalse(any("__pycache__" in n or n.startswith(".git/") for n in nombres))

    def test_mismos_archivos_producen_mismo_zip(self):
        a, b = self.carpeta / "a.zip", self.carpeta / "b.zip"
        self.assertEqual(crear_paquete(a), crear_paquete(b))
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_detecta_modificacion_de_un_archivo(self):
        original = self.carpeta / "original.zip"
        alterado = self.carpeta / "alterado.zip"
        crear_paquete(original)
        with zipfile.ZipFile(original) as entrada, zipfile.ZipFile(alterado, "w") as salida:
            for info in entrada.infolist():
                datos = b"alterado" if info.filename == "requirements.txt" else entrada.read(info.filename)
                salida.writestr(info, datos)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verificar_paquete(alterado)

    def test_rechaza_rutas_que_salgan_de_la_entrega(self):
        archivo = self.carpeta / "invalido.zip"
        with zipfile.ZipFile(archivo, "w") as salida:
            salida.writestr("../fuera.txt", "no se debe extraer")
        with self.assertRaisesRegex(ValueError, "ruta no válida"):
            verificar_paquete(archivo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
