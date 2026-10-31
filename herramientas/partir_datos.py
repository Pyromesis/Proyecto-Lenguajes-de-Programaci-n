#!/usr/bin/env python3
"""AREPA - Partición reproducible de un CSV en entrenamiento y prueba.

La separación se hace por hash SHA-256 de ``semilla:indice``. Así el
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

import argparse
import csv
import hashlib
import pathlib
import sys


def _clave(semilla: int, indice: int) -> str:
    return hashlib.sha256("{0}:{1}".format(semilla, indice).encode("utf-8")).hexdigest()


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
        lector = csv.reader(fh)
        filas = list(lector)
    if not filas:
        raise ValueError("el archivo está vacío: {0}".format(ruta))
    return filas[0], filas[1:]


def _escribir(ruta: pathlib.Path, encabezado, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh, lineterminator="\n")
        escritor.writerow(encabezado)
        escritor.writerows(filas)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    analizador = argparse.ArgumentParser(
        description="Divide un CSV en entrenamiento y prueba de forma reproducible."
    )
    analizador.add_argument("archivo", help="CSV de entrada")
    analizador.add_argument(
        "--salida-dir",
        default="datos/particiones",
        help="directorio de salida (por defecto: datos/particiones)",
    )
    analizador.add_argument(
        "--proporcion-prueba",
        type=float,
        default=0.2,
        help="fracción de filas para prueba, entre 0 y 1 (por defecto: 0.2)",
    )
    analizador.add_argument(
        "--semilla",
        type=int,
        default=2026,
        help="semilla del hash determinista (por defecto: 2026)",
    )
    argumentos = analizador.parse_args(argv)

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
