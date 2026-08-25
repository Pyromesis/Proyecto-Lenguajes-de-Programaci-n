"""
AREPA - Corredor maestro de pruebas
-----------------------------------
Ejecuta las cuatro suites del proyecto en orden:
  1. front-end (lexer/parser ANTLR4 + diagnóstico propio);
  2. biblioteca propia de datos (lector CSV, Tabla, tipos);
  3. evaluador de expresiones propio;
  4. runtime propio (programas completos del DSL).

Uso:
    python pruebas/test_proyecto.py
"""

import os
import sys
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUITES = (
    ("Front-end (léxico y sintáctico)", "test_front.py"),
    ("Biblioteca propia de datos", "test_datos.py"),
    ("Evaluador de expresiones propio", "test_expresiones.py"),
    ("Runtime propio (programas completos)", "test_runtime.py"),
)


def main():
    total_ok = 0
    fallidas = []
    for titulo, archivo in SUITES:
        print("\n" + "#" * 78)
        print("# SUITE: {0} ({1})".format(titulo, archivo))
        print("#" * 78 + "\n")
        resultado = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "pruebas", archivo)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        salida = resultado.stdout or ""
        print(salida)
        if resultado.returncode == 0:
            total_ok += 1
        else:
            fallidas.append(titulo)
            if resultado.stderr:
                print("SALIDA DE ERROR:\n" + resultado.stderr)

    print("\n" + "=" * 78)
    print(" RESUMEN GENERAL: {0} de {1} suites pasaron".format(total_ok, len(SUITES)))
    print("=" * 78)
    if fallidas:
        print("Suites con fallos: " + ", ".join(fallidas))
        return 1
    print("¡De una! Toda la biblioteca propia pasó sus pruebas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
