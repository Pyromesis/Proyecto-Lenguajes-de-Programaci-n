"""
AREPA - Pruebas unitarias de las utilidades propias (src/utiles/)
-----------------------------------------------------------------
Prueba matematica.py, texto.py, binario.py y sha256.py, que reemplazan a
los módulos 'math', 're', 'unicodedata', 'struct' y 'hashlib' dentro de
la biblioteca. Aquí esos módulos de Python se usan SOLO como oráculo
independiente para comparar resultados; la biblioteca no los importa
(lo verifica la prueba 'la_biblioteca_no_importa_modulos_reemplazados').

Uso:
    python3 pruebas/test_utiles.py
"""

import hashlib
import math
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from utiles.binario import GRANDE, PEQUENO, bytes_a_entero, entero_a_bytes  # noqa: E402
from utiles.matematica import (  # noqa: E402
    es_finito,
    exponente_decimal,
    piso,
    raiz_cuadrada,
    raiz_entera,
    techo,
)
from utiles.sha256 import sha256_hex  # noqa: E402
from utiles.texto import colapsar_espacios, es_identificador, quitar_tildes  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


def _serie(semilla, cantidad):
    """Generador congruencial propio: números reproducibles sin 'random'."""
    estado = semilla
    for _ in range(cantidad):
        estado = (estado * 1103515245 + 12345) % (1 << 31)
        yield estado


# ---------------------------------------------------------------------- #
# matematica.py
# ---------------------------------------------------------------------- #

@caso
def es_finito_distingue_infinito_y_nan():
    assert es_finito(0) and es_finito(-2.5) and es_finito(10 ** 40)
    assert not es_finito(float("inf"))
    assert not es_finito(float("-inf"))
    assert not es_finito(float("nan"))
    assert not es_finito("hola")


@caso
def piso_y_techo_casos_borde():
    assert piso(2.7) == 2 and techo(2.2) == 3
    assert piso(-2.2) == -3 and techo(-2.7) == -2
    assert piso(5.0) == 5 and techo(5.0) == 5
    assert piso(-0.0) == 0 and techo(0.0) == 0
    assert isinstance(piso(2.7), int) and isinstance(techo(2.2), int)


@caso
def piso_y_techo_coinciden_con_math():
    for crudo in _serie(7, 5000):
        valor = (crudo - (1 << 30)) / 997.0
        assert piso(valor) == math.floor(valor), valor
        assert techo(valor) == math.ceil(valor), valor


@caso
def piso_rechaza_no_finitos():
    for funcion in (piso, techo):
        try:
            funcion(float("inf"))
            raise AssertionError("debió rechazar el infinito")
        except ValueError:
            pass


@caso
def raiz_entera_exacta_en_cuadrados_y_vecinos():
    for n in range(0, 2000):
        assert raiz_entera(n) == math.isqrt(n), n
    for base in (10 ** 9, 10 ** 15, 12345678901234567890):
        assert raiz_entera(base * base) == base
        assert raiz_entera(base * base - 1) == base - 1
        assert raiz_entera(base * base + 1) == base


@caso
def raiz_entera_rechaza_negativos_y_no_enteros():
    for malo in (-1, 2.5, True):
        try:
            raiz_entera(malo)
            raise AssertionError("debió rechazar {0!r}".format(malo))
        except ValueError:
            pass


@caso
def raiz_cuadrada_newton_precisa():
    assert raiz_cuadrada(0) == 0
    assert raiz_cuadrada(144) == 12
    assert raiz_cuadrada(0.25) == 0.5
    for crudo in _serie(11, 2000):
        valor = crudo / 1000.0 + 1e-6
        esperado = math.sqrt(valor)
        assert abs(raiz_cuadrada(valor) - esperado) <= 1e-12 * esperado, valor
    try:
        raiz_cuadrada(-4)
        raise AssertionError("debió rechazar el negativo")
    except ValueError:
        pass


@caso
def exponente_decimal_potencias_exactas():
    for k in range(-12, 13):
        assert exponente_decimal(10.0 ** k) == k, k
    assert exponente_decimal(999.999) == 2
    assert exponente_decimal(0.0999) == -2
    assert exponente_decimal(7) == 0


@caso
def exponente_decimal_coincide_con_log10():
    for crudo in _serie(3, 5000):
        valor = (crudo + 1) / 12345.0
        assert exponente_decimal(valor) == math.floor(math.log10(valor)), valor
    for malo in (0, -5, float("inf")):
        try:
            exponente_decimal(malo)
            raise AssertionError("debió rechazar {0!r}".format(malo))
        except ValueError:
            pass


# ---------------------------------------------------------------------- #
# texto.py
# ---------------------------------------------------------------------- #

@caso
def identificadores_validos():
    for nombre in ("x", "_tmp", "total_2026", "año", "niño_1", "Ventas", "__"):
        assert es_identificador(nombre), nombre


@caso
def identificadores_invalidos():
    for nombre in ("", "1x", "a-b", "a b", " a", "a.b", "x!", 42, None):
        assert not es_identificador(nombre), nombre


@caso
def colapsar_espacios_une_blancos():
    assert colapsar_espacios("  a \t\n b   c ") == "a b c"
    assert colapsar_espacios("") == ""
    assert colapsar_espacios("   ") == ""
    assert colapsar_espacios("uno") == "uno"


@caso
def quitar_tildes_espanol():
    assert quitar_tildes("Bogotá, Ñandú y pingüino") == "Bogota, Nandu y pinguino"
    assert quitar_tildes("ÁÉÍÓÚ áéíóú Üü Ññ") == "AEIOU aeiou Uu Nn"
    assert quitar_tildes("sin cambios 123") == "sin cambios 123"


@caso
def quitar_tildes_descarta_marcas_combinantes():
    descompuesto = "canción"  # o + tilde combinante suelta
    assert quitar_tildes(descompuesto) == "cancion"
    assert quitar_tildes("¿ñ?") == "¿n?"  # los signos los resuelve la fuente


# ---------------------------------------------------------------------- #
# binario.py
# ---------------------------------------------------------------------- #

@caso
def entero_a_bytes_coincide_con_struct():
    for valor in (0, 1, 255, 256, 800, 0xDEADBEEF, 0xFFFFFFFF):
        assert entero_a_bytes(valor, 4, GRANDE) == struct.pack(">I", valor)
        assert entero_a_bytes(valor, 4, PEQUENO) == struct.pack("<I", valor)
    for valor in (0, 1, 0xFFFE, 0xFFFF):
        assert entero_a_bytes(valor, 2, PEQUENO) == struct.pack("<H", valor)


@caso
def bytes_a_entero_es_inverso():
    for crudo in _serie(5, 500):
        assert bytes_a_entero(entero_a_bytes(crudo, 4, GRANDE), GRANDE) == crudo
        assert bytes_a_entero(entero_a_bytes(crudo, 4, PEQUENO), PEQUENO) == crudo
    assert bytes_a_entero(b"\x00\x00\x03\x20") == 800


@caso
def entero_a_bytes_rechaza_desbordes():
    for valor, cantidad in ((256, 1), (-1, 2), (1 << 32, 4), (2.0, 4)):
        try:
            entero_a_bytes(valor, cantidad)
            raise AssertionError("debió rechazar {0!r}".format(valor))
        except ValueError:
            pass
    try:
        entero_a_bytes(1, 2, "raro")
        raise AssertionError("debió rechazar el orden desconocido")
    except ValueError:
        pass


# ---------------------------------------------------------------------- #
# sha256.py
# ---------------------------------------------------------------------- #

@caso
def sha256_vectores_oficiales():
    assert sha256_hex(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855"
    )
    assert sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


@caso
def sha256_coincide_con_hashlib_en_bordes_de_bloque():
    for largo in (1, 54, 55, 56, 57, 63, 64, 65, 119, 120, 500):
        mensaje = bytes((i * 7 + 3) % 256 for i in range(largo))
        assert sha256_hex(mensaje) == hashlib.sha256(mensaje).hexdigest(), largo
    clave = "2026:17".encode("utf-8")
    assert sha256_hex(clave) == hashlib.sha256(clave).hexdigest()


# ---------------------------------------------------------------------- #
# Regla del proyecto: la biblioteca solo depende de ANTLR4
# ---------------------------------------------------------------------- #

@caso
def la_biblioteca_no_importa_modulos_reemplazados():
    """Ningún archivo de src/ importa lo que se reimplementó ni terceros."""
    prohibidos = (
        "math", "re", "struct", "unicodedata", "csv", "hashlib", "argparse",
        "glob", "codecs", "random", "statistics", "zlib", "json", "decimal",
        "fractions", "collections", "itertools", "functools",
        "pandas", "numpy", "matplotlib", "sklearn", "scipy", "PIL",
    )
    hallazgos = []
    carpeta_src = os.path.join(RAIZ, "src")
    for carpeta, _, archivos in os.walk(carpeta_src):
        for nombre in archivos:
            if not nombre.endswith(".py"):
                continue
            ruta = os.path.join(carpeta, nombre)
            with open(ruta, "r", encoding="utf-8") as manejador:
                for numero, linea in enumerate(manejador, 1):
                    palabras = linea.strip().split()
                    if len(palabras) < 2 or palabras[0] not in ("import", "from"):
                        continue
                    modulo = palabras[1].split(".")[0].rstrip(",")
                    if modulo in prohibidos:
                        hallazgos.append(
                            "{0}:{1} importa {2}".format(
                                os.path.relpath(ruta, RAIZ), numero, modulo
                            )
                        )
    assert not hallazgos, "; ".join(hallazgos)


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE LAS UTILIDADES PROPIAS (matemática, texto, bytes, SHA-256)")
    print("=" * 78)
    for funcion in CASOS:
        try:
            funcion()
            pasaron += 1
            print("[PASÓ ] {0}".format(funcion.__name__))
        except AssertionError as problema:
            fallaron += 1
            print("[FALLÓ] {0}: {1}".format(funcion.__name__, problema))
        except Exception as problema:
            fallaron += 1
            print("[FALLÓ] {0}: excepción {1}".format(funcion.__name__, problema))
    print("-" * 78)
    print("Resultado: {0} de {1} pasaron".format(pasaron, len(CASOS)))
    return 0 if fallaron == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
