"""
AREPA - Analizador del front-end (src/lenguaje/analizador.py)
-------------------------------------------------------------
Orquesta el análisis léxico y sintáctico con el lexer/parser generado
por ANTLR4 (uso autorizado) y el listener de errores propio.

Devuelve (parser, arbol, errores): los errores combinan hallazgos
léxicos y sintácticos con línea, columna y mensaje en español.
"""

import os
import sys

_RUTA_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_SRC = os.path.dirname(_RUTA_AQUI)
_GENERADO = os.path.join(_RAIZ_SRC, "..", "generado")
for _ruta in (_GENERADO, _RAIZ_SRC):
    _absoluta = os.path.abspath(_ruta)
    if _absoluta not in sys.path:
        sys.path.insert(0, _absoluta)

from antlr4 import CommonTokenStream, InputStream  # noqa: E402

from ArepaLexer import ArepaLexer  # noqa: E402
from ArepaParser import ArepaParser  # noqa: E402

from lenguaje.errores import ErroresArepa  # noqa: E402


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
    return parser, arbol, _sin_duplicados(errores)


def _sin_duplicados(errores):
    """Quita errores exactamente iguales (mismo tipo, posición y mensaje)."""
    unicos = []
    vistos = set()
    for error in errores:
        clave = (error["tipo"], error["linea"], error["columna"], error["mensaje"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(error)
    return unicos
