"""
AREPA - Interfaz de línea de comandos (Fase 1: front-end)
---------------------------------------------------------
Ejecuta el análisis léxico y sintáctico de un programa escrito en el
lenguaje AREPA y reporta los errores con línea y columna.

Uso:
    python src/main.py <archivo.arepa> [--arbol] [--tokens]

Códigos de salida:
    0 - el programa es válido
    1 - el programa tiene errores léxicos o sintácticos
    2 - no se pudo leer el archivo
"""

import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "generado"))

from antlr4 import CommonTokenStream, InputStream  # noqa: E402
from antlr4.error.ErrorListener import ConsoleErrorListener  # noqa: E402

from ArepaLexer import ArepaLexer  # noqa: E402
from ArepaParser import ArepaParser  # noqa: E402

from arbol import contar_sentencias, imprimir_arbol  # noqa: E402
from errores import ErroresArepa  # noqa: E402

VERSION = "AREPA v0.1 (Fase 1 - front-end)"
LINEA = "=" * 62


def analizar(texto):
    """Ejecuta el análisis completo sobre un texto fuente.

    Devuelve una tupla (parser, arbol, errores) donde errores combina
    los hallazgos léxicos y sintácticos.
    """
    entrada = InputStream(texto)

    # ---- Análisis léxico ----
    lexer = ArepaLexer(entrada)
    lexer.removeErrorListeners()
    error_lexico = ErroresArepa(ErroresArepa.LEXICO)
    lexer.addErrorListener(error_lexico)

    flujo = CommonTokenStream(lexer)
    flujo.fill()

    # ---- Análisis sintáctico ----
    parser = ArepaParser(flujo)
    parser.removeErrorListeners()
    error_sintactico = ErroresArepa(ErroresArepa.SINTACTICO)
    parser.addErrorListener(error_sintactico)

    arbol = parser.programa()

    errores = list(error_lexico.errores) + list(error_sintactico.errores)
    return parser, arbol, errores


def volcar_tokens(parser):
    """Imprime la tabla de tokens producida por el lexer."""
    flujo = parser.getTokenStream()
    nombres = ArepaLexer.symbolicNames
    print("\n{0:<14} {1:<18} {2:>6} {3:>9}".format("TOKEN", "TEXTO", "LÍNEA", "COLUMNA"))
    print("-" * 52)
    for tok in flujo.tokens:
        if tok.type == -1:
            etiqueta = "<EOF>"
        else:
            etiqueta = (
                nombres[tok.type]
                if 0 <= tok.type < len(nombres)
                else str(tok.type)
            )
        texto = tok.text.replace("\n", "\\n").replace("\r", "")
        if len(texto) > 16:
            texto = texto[:13] + "..."
        print("{0:<14} {1:<18} {2:>6} {3:>9}".format(etiqueta, texto, tok.line, tok.column))
    print()


def main():
    analizador = argparse.ArgumentParser(
        prog="arepa",
        description="Front-end del lenguaje AREPA: análisis léxico y sintáctico.",
    )
    analizador.add_argument("archivo", help="programa fuente (.arepa)")
    analizador.add_argument("--arbol", action="store_true", help="muestra el árbol de análisis")
    analizador.add_argument("--tokens", action="store_true", help="muestra la lista de tokens")
    argumentos = analizador.parse_args()

    print(LINEA)
    print(" {0}".format(VERSION))
    print(LINEA)

    if not os.path.isfile(argumentos.archivo):
        print("Paila: no encontré el archivo '{0}'.".format(argumentos.archivo))
        return 2

    with open(argumentos.archivo, "r", encoding="utf-8-sig") as manejador:
        texto = manejador.read()

    print("Archivo : {0}".format(argumentos.archivo))

    try:
        parser, arbol, errores = analizar(texto)
    except Exception as problema:  # protección ante fallos internos
        print("Error interno del front-end: {0}".format(problema))
        return 1

    if argumentos.tokens:
        volcar_tokens(parser)

    if errores:
        print("\nEncontré {0} problema(s), revisá esto:".format(len(errores)))
        for e in errores:
            print(
                "  [{0}] Línea {1}, Columna {2}: {3}".format(
                    e["tipo"], e["linea"], e["columna"], e["mensaje"]
                )
            )
        print("\nChévere lo intentaste, pero el programa quedó mal escrito. Corregí y volvé a intentar.")
        return 1

    sentencias = contar_sentencias(arbol)
    print("Análisis léxico   : OK ({0} tokens)".format(len(parser.getTokenStream().tokens)))
    print("Análisis sintáctico: OK")
    print("¡Quihubo pues! Programa bien escrito: {0} sentencia(s) reconocida(s).".format(sentencias))

    if argumentos.arbol:
        print()
        imprimir_arbol(arbol, parser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
