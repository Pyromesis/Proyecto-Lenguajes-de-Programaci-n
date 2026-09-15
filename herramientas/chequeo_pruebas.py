#!/usr/bin/env python3
"""AREPA - Chequeo del conteo de pruebas (Linux).

Fuente única de verdad del número de pruebas: ejecuta las 6 suites,
extrae el "N de N" reportado por cada una y lo compara contra el conteo
canónico. Si algún total cambia (nueva prueba agregada o eliminada),
este script falla y obliga a actualizar el conteo en un solo lugar:
la tabla ESPERADO de abajo y los documentos que la citan
(README §Pruebas, docs/04 §1, docs/05 §8, docs/08 §1-§2, docs/10 §1-§2).

Uso:
    python3 herramientas/chequeo_pruebas.py
"""

import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Conteo canónico: (archivo de suite, pruebas esperadas).
# Total: 48 + 21 + 43 + 16 + 15 + 51 = 194.
ESPERADO = (
    ("test_front.py", 48),
    ("test_arbol.py", 21),
    ("test_datos.py", 43),
    ("test_expresiones.py", 16),
    ("test_simbolos.py", 15),
    ("test_runtime.py", 51),
)

PATRON = re.compile(r"Resultado:\s*(\d+)\s+de\s+(\d+)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _limpia(salida):
    """Quita códigos de color ANSI para comparar texto plano."""
    return ANSI.sub("", salida or "")


def contar_suite(archivo):
    """Corre una suite y devuelve (pasadas, totales) según su línea Resultado."""
    resultado = subprocess.run(
        [sys.executable, os.path.join(RAIZ, "pruebas", archivo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    salida = _limpia(resultado.stdout)
    coincidencias = PATRON.findall(salida)
    if resultado.returncode != 0 or not coincidencias:
        print("FALLO: {0} no terminó limpio o sin línea 'Resultado'.".format(archivo))
        if resultado.stderr:
            print(resultado.stderr[-2000:])
        return None
    pasadas, totales = (int(x) for x in coincidencias[-1])
    return pasadas, totales


def main():
    total = 0
    ok = True
    for archivo, esperado in ESPERADO:
        obtenido = contar_suite(archivo)
        if obtenido is None:
            ok = False
            continue
        pasadas, totales = obtenido
        total += totales
        estado = "OK" if (pasadas, totales) == (esperado, esperado) else "DESCUADRE"
        if estado != "OK":
            ok = False
        print("{0}: {1} de {2} (canónico: {3}) [{4}]".format(
            archivo, pasadas, totales, esperado, estado))
    canonico = sum(e for _, e in ESPERADO)
    print("Total: {0} (canónico: {1})".format(total, canonico))
    if not ok or total != canonico:
        print("DESUNIFICADO: actualizá ESPERADO aquí y los docs que citan el conteo.")
        return 1
    print("Unificado: 6 suites, 194 pruebas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
