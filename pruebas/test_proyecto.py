"""
AREPA - Corredor maestro de pruebas
-----------------------------------
Ejecuta las ocho suites del proyecto en orden:
  1. front-end (lexer/parser ANTLR4 + diagnóstico propio);
  2. estructura del árbol de análisis;
  3. biblioteca propia de datos (lector CSV, Tabla, tipos);
  4. estructuras propias (listas, registros y tablas en memoria);
  5. evaluador de expresiones propio;
  6. tabla de símbolos y contexto propios;
  7. runtime propio (programas completos del DSL);
  8. motor gráfico y visualización propia (PNG, escalas, lienzo).

Uso:
    python3 pruebas/test_proyecto.py

Si existe `.venv/bin/python`, el corredor lo usa para las suites (es el
intérprete que trae antlr4 en una instalación limpia).
"""

import os
import sys
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUITES = (
    ("Front-end (léxico y sintáctico)", "test_front.py"),
    ("Estructura del árbol de análisis", "test_arbol.py"),
    ("Biblioteca propia de datos", "test_datos.py"),
    ("Estructuras propias (listas, registros, tablas)", "test_estructuras.py"),
    ("Evaluador de expresiones propio", "test_expresiones.py"),
    ("Tabla de símbolos y contexto propios", "test_simbolos.py"),
    ("Runtime propio (programas completos)", "test_runtime.py"),
    ("Motor gráfico y visualización propia", "test_graficas.py"),
)


def _interprete():
    """Devuelve el intérprete con antlr4: .venv si existe, si no el actual."""
    ruta_venv = os.path.join(RAIZ, ".venv", "bin", "python")
    if os.path.exists(ruta_venv):
        return ruta_venv
    return sys.executable


def main():
    total_ok = 0
    fallidas = []
    interprete = _interprete()
    for titulo, archivo in SUITES:
        print("\n" + "#" * 78)
        print("# SUITE: {0} ({1})".format(titulo, archivo))
        print("#" * 78 + "\n")
        resultado = subprocess.run(
            [interprete, os.path.join(RAIZ, "pruebas", archivo)],
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
