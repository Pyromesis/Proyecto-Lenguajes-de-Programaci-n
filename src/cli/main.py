"""
AREPA - Interfaz de línea de comandos (src/cli/main.py)
-------------------------------------------------------
Dos modos:

  * Validación (por defecto, Fase 1): análisis léxico y sintáctico del
    programa con el lexer/parser de ANTLR4 y el listener propio; reporta
    los errores con línea y columna.

  * Ejecución (--ejecutar): tras validar, interpreta el programa con el
    runtime propio (runtime/, datos/, expresiones/): carga CSV con el
    lector propio, aplica el pipeline sobre la Tabla propia y evalúa
    expresiones con el evaluador propio. 'pinte' se valida pero no
    genera imágenes (Fase 3).

Uso:
    python src/cli/main.py <archivo.arepa> [--arbol] [--tokens] [--ejecutar]

Códigos de salida:
    0 - el programa es válido (y se ejecutó sin errores si --ejecutar)
    1 - el programa tiene errores léxicos, sintácticos o de ejecución
    2 - no se pudo leer el archivo
"""

import argparse
import os
import sys

_RUTA_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_SRC = os.path.dirname(_RUTA_AQUI)
for _ruta in (_RAIZ_SRC, os.path.join(_RAIZ_SRC, "..", "generado")):
    _absoluta = os.path.abspath(_ruta)
    if _absoluta not in sys.path:
        sys.path.insert(0, _absoluta)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lenguaje.analizador import analizar  # noqa: E402
from lenguaje.arbol import contar_sentencias, imprimir_arbol  # noqa: E402
from errores_base import ErrorArepa, RetornoFuncion  # noqa: E402

VERSION = "AREPA v0.2 (Fase 1 - front-end + biblioteca propia)"
LINEA = "=" * 62


def volcar_tokens(parser):
    """Imprime la tabla de tokens producida por el lexer."""
    from ArepaLexer import ArepaLexer

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
        description="Front-end y runtime del lenguaje AREPA.",
    )
    analizador.add_argument("archivo", help="programa fuente (.arepa)")
    analizador.add_argument("--arbol", action="store_true", help="muestra el árbol de análisis")
    analizador.add_argument("--tokens", action="store_true", help="muestra la lista de tokens")
    analizador.add_argument(
        "--ejecutar",
        action="store_true",
        help="ejecuta el programa con la biblioteca propia (datos, expresiones, runtime)",
    )
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

    if argumentos.ejecutar:
        print("\n" + "-" * 62)
        print(" Ejecución con la biblioteca propia")
        print("-" * 62)
        return _ejecutar(arbol)

    return 0


def _ejecutar(arbol):
    """Corre el programa con el runtime propio y reporta errores claros."""
    from runtime.ejecutor import EjecutorArepa

    ejecutor = EjecutorArepa()
    try:
        ejecutor.ejecutar(arbol)
    except ErrorArepa as problema:
        ejecutor.contexto.registrar_error(problema)
        etiqueta = type(problema).__name__
        mapa = {
            "ErrorSemantico": "semántico",
            "ErrorVariable": "semántico",
            "ErrorColumna": "semántico",
            "ErrorTipos": "semántico",
            "ErrorOperacion": "semántico",
            "ErrorEjecucion": "ejecución",
            "ErrorArchivo": "ejecución",
            "ErrorCSV": "ejecución",
        }
        print("\nError de {0} durante la ejecución:".format(mapa.get(etiqueta, "ejecución")))
        print("  {0}".format(problema))
        if problema.contexto:
            print("  Contexto: {0}".format(problema.contexto))
        print("\nUy, el programa se cayó. Corregí y volvé a intentar.")
        return 1
    except RetornoFuncion:
        print("\nError semántico: 'devuelva' solo funciona dentro de una función.")
        return 1

    print("\n¡De una! El programa corrió completo sin tropiezos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
