#!/usr/bin/env python3
"""AREPA - Partición reproducible de un CSV en entrenamiento y prueba.

La separación se hace por hash SHA-256 de ``semilla:indice`` (SHA-256, lector CSV y análisis de
argumentos propios: sin ``hashlib``, ``csv`` ni ``argparse``). Así el
resultado no depende del sistema operativo, de la versión de Python ni del
orden de un generador pseudoaleatorio: la misma entrada, semilla y proporción
producen siempre los mismos archivos.

Uso:
    python3 herramientas/partir_datos.py datos/casas_ml.csv
    python3 herramientas/partir_datos.py datos/casas_ml.csv \\
        --salida-dir datos/particiones --proporcion-prueba 0.2 --semilla 2026

Escribe ``<nombre>_entrenamiento.csv`` y ``<nombre>_prueba.csv`` en el
directorio indicado (por defecto ``datos/particiones``).
"""

from __future__ import annotations

import pathlib
import sys

_RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(_RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(_RAIZ / "src"))

from utiles.sha256 import sha256_hex  # noqa: E402  (SHA-256 propio)


def _clave(semilla: int, indice: int) -> str:
    return sha256_hex("{0}:{1}".format(semilla, indice).encode("utf-8"))


def leer_csv_crudo(texto: str):
    """Lector CSV propio (máquina de estados): devuelve filas de textos.

    Respeta campos entre comillas dobles, comillas escapadas ("") y saltos
    de línea dentro de un campo entrecomillado. No convierte tipos: aquí
    solo se reparten filas, así que cada celda se conserva como texto.
    """
    filas, fila, campo = [], [], []
    en_comillas = False
    hubo_contenido = False
    i, total = 0, len(texto)
    while i < total:
        c = texto[i]
        if en_comillas:
            if c == '"':
                if i + 1 < total and texto[i + 1] == '"':
                    campo.append('"')
                    i += 1
                else:
                    en_comillas = False
            else:
                campo.append(c)
        elif c == '"':
            en_comillas = True
            hubo_contenido = True
        elif c == ",":
            fila.append("".join(campo))
            campo = []
            hubo_contenido = True
        elif c == "\n" or c == "\r":
            if c == "\r" and i + 1 < total and texto[i + 1] == "\n":
                i += 1
            if hubo_contenido or campo:
                fila.append("".join(campo))
                filas.append(fila)
            fila, campo, hubo_contenido = [], [], False
        else:
            campo.append(c)
        i += 1
    if hubo_contenido or campo:
        fila.append("".join(campo))
        filas.append(fila)
    return filas


def _celda_csv(valor: str) -> str:
    """Entrecomilla la celda solo si hace falta (coma, comilla o salto)."""
    if any(c in valor for c in (",", '"', "\n", "\r")):
        return '"' + valor.replace('"', '""') + '"'
    return valor


def partir(filas, proporcion_prueba: float, semilla: int):
    """Devuelve (entrenamiento, prueba) conservando el orden original."""
    if not 0 < proporcion_prueba < 1:
        raise ValueError("la proporción de prueba debe estar entre 0 y 1")
    if len(filas) < 2:
        raise ValueError("se necesitan al menos 2 filas para partir el archivo")

    total_prueba = int(round(len(filas) * proporcion_prueba))
    total_prueba = max(1, min(len(filas) - 1, total_prueba))
    ordenadas = sorted(
        range(len(filas)), key=lambda i: (_clave(semilla, i), i)
    )
    indices_prueba = set(ordenadas[:total_prueba])
    entrenamiento = [fila for i, fila in enumerate(filas) if i not in indices_prueba]
    prueba = [fila for i, fila in enumerate(filas) if i in indices_prueba]
    return entrenamiento, prueba


def _leer(ruta: pathlib.Path):
    with ruta.open("r", encoding="utf-8-sig", newline="") as fh:
        filas = leer_csv_crudo(fh.read())
    if not filas:
        raise ValueError("el archivo está vacío: {0}".format(ruta))
    return filas[0], filas[1:]


def _escribir(ruta: pathlib.Path, encabezado, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        for fila in [encabezado] + list(filas):
            fh.write(",".join(_celda_csv(celda) for celda in fila) + "\n")


USO = """uso: partir_datos.py <archivo.csv> [--salida-dir DIR]
                       [--proporcion-prueba P] [--semilla N]

  archivo               CSV de entrada
  --salida-dir DIR      directorio de salida (por defecto: datos/particiones)
  --proporcion-prueba P fracción de filas para prueba, entre 0 y 1 (0.2)
  --semilla N           semilla del hash determinista (2026)
  -h, --ayuda           muestra esta ayuda"""


class _Argumentos:
    def __init__(self):
        self.archivo = None
        self.salida_dir = "datos/particiones"
        self.proporcion_prueba = 0.2
        self.semilla = 2026


def _leer_argumentos(lista):
    """Analizador propio de la línea de comandos (None = pidió ayuda)."""
    argumentos = _Argumentos()
    i = 0
    while i < len(lista):
        texto = lista[i]
        if texto in ("-h", "--ayuda", "--help"):
            return None
        if texto in ("--salida-dir", "--proporcion-prueba", "--semilla"):
            if i + 1 >= len(lista):
                raise ValueError("a la opción {0} le falta su valor".format(texto))
            valor = lista[i + 1]
            i += 1
            try:
                if texto == "--salida-dir":
                    argumentos.salida_dir = valor
                elif texto == "--proporcion-prueba":
                    argumentos.proporcion_prueba = float(valor)
                else:
                    argumentos.semilla = int(valor)
            except ValueError:
                raise ValueError(
                    "el valor '{0}' no sirve para {1}".format(valor, texto)
                )
        elif texto.startswith("--"):
            raise ValueError("no conozco la opción {0}".format(texto))
        elif argumentos.archivo is None:
            argumentos.archivo = texto
        else:
            raise ValueError("solo se recibe un archivo; sobra '{0}'".format(texto))
        i += 1
    if argumentos.archivo is None:
        raise ValueError("falta el archivo CSV de entrada")
    return argumentos


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        argumentos = _leer_argumentos(sys.argv[1:] if argv is None else argv)
    except ValueError as exc:
        print("Paila: {0}.".format(exc))
        print(USO)
        return 2
    if argumentos is None:
        print(USO)
        return 0

    entrada = pathlib.Path(argumentos.archivo)
    if not entrada.is_file():
        print("Paila: no encontré el archivo '{0}'.".format(entrada))
        return 2

    try:
        encabezado, filas = _leer(entrada)
        entrenamiento, prueba = partir(
            filas, argumentos.proporcion_prueba, argumentos.semilla
        )
    except ValueError as exc:
        print("Paila: {0}.".format(exc))
        return 1

    salida = pathlib.Path(argumentos.salida_dir)
    base = entrada.stem
    ruta_entrenamiento = salida / "{0}_entrenamiento.csv".format(base)
    ruta_prueba = salida / "{0}_prueba.csv".format(base)
    _escribir(ruta_entrenamiento, encabezado, entrenamiento)
    _escribir(ruta_prueba, encabezado, prueba)

    print(
        "Partición reproducible: {0} fila(s) → {1} entrenamiento + {2} prueba."
        .format(len(filas), len(entrenamiento), len(prueba))
    )
    print("  {0}".format(ruta_entrenamiento))
    print("  {0}".format(ruta_prueba))
    print(
        "  semilla={0}, proporción_prueba={1}".format(
            argumentos.semilla, argumentos.proporcion_prueba
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
