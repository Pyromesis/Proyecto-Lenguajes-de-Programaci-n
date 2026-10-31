"""
AREPA - Interfaz de línea de comandos (src/cli/main.py)
-------------------------------------------------------
Dos modos:

  * Validación (por defecto, Cortes 1-2): análisis léxico y sintáctico del
    programa con el lexer/parser de ANTLR4 y el listener propio; reporta
    los errores con línea y columna.

  * Ejecución (--ejecutar): tras validar, interpreta el programa con el
    runtime propio (runtime/, datos/, expresiones/) y produce los
    archivos que pida el programa: CSV con 'guarde' y PNG con 'pinte'
    (Fase 3: motor gráfico propio). Con '--sin-ventana' no se abre
    ningún visor externo, útil en CI o en demostraciones sin entorno
    gráfico.

Uso:
    python3 src/cli/main.py <archivo.arepa> [--arbol] [--tokens]
                            [--ejecutar] [--sin-ventana]

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

VERSION = "AREPA v0.4 (Fase 3 - visualizacion y producto final)"
LINEA = "=" * 62
SANGRIAS_TAB = 4


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


def _mostrar_contexto(texto, linea, columna):
    """Muestra la línea fuente con un caret alineado bajo la columna.

    Ejemplo::

          Línea 4: c = = 3
                     ^

    No imprime nada si la columna es desconocida (negativa) o si la
    línea no existe en el programa. Los tabuladores se expanden a cuatro
    espacios tanto en la línea como en la sangría del caret, para que el
    caret quede alineado aunque la fuente use tabs.
    """
    if columna < 0 or linea < 1:
        return

    lineas = texto.splitlines()
    if linea > len(lineas):
        return

    original = lineas[linea - 1]
    columna = min(columna, len(original))
    fuente = original.replace("\t", " " * SANGRIAS_TAB)
    prefijo = "  Línea {0}: ".format(linea)
    # Ancho (en pantalla) de lo que hay antes de la columna, ya con los
    # tabuladores expandidos, para que el caret quede alineado.
    ancho_previo = len(original[:columna].replace("\t", " " * SANGRIAS_TAB))
    print("{0}{1}".format(prefijo, fuente))
    print("{0}^".format(" " * (len(prefijo) + ancho_previo)))


def _resumen_archivos(contexto):
    """Lista los CSV/PNG producidos por el programa, si hubo alguno."""
    registros = getattr(contexto, "archivos_generados", None) or ()
    if not registros:
        return
    print("\nArchivos generados:")
    for registro in registros:
        print(
            "  - {0} ({1}, {2} bytes)".format(
                registro.get("ruta", "?"),
                registro.get("tipo", "?"),
                registro.get("bytes", 0),
            )
        )


def main():
    analizador = argparse.ArgumentParser(
        prog="arepa",
        usage="arepa <archivo> [opciones]",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Front-end y runtime del lenguaje AREPA.\n"
            "Valida el programa y, con --ejecutar, lo corre con la biblioteca\n"
            "propia (datos, expresiones, runtime y motor gráfico)."
        ),
        epilog=(
            "Ejemplos:\n"
            "  arepa ejemplos/demo.arepa --ejecutar\n"
            "  arepa ejemplos/graficas.arepa --ejecutar --sin-ventana\n"
            "  arepa ejemplos/demo.arepa --arbol --tokens"
        ),
    )
    analizador._positionals.title = "argumentos"
    analizador._optionals.title = "opciones"
    analizador.add_argument("archivo", help="programa fuente (.arepa)")
    analizador.add_argument(
        "-h",
        "--ayuda",
        "--help",
        action="help",
        help="muestra esta ayuda y sale",
    )
    analizador.add_argument(
        "--version",
        action="version",
        version=VERSION,
        help="muestra la versión y sale",
    )
    analizador.add_argument(
        "--arbol", action="store_true", help="muestra el árbol de análisis"
    )
    analizador.add_argument(
        "--tokens", action="store_true", help="muestra la lista de tokens"
    )
    analizador.add_argument(
        "--ejecutar",
        action="store_true",
        help="ejecuta el programa con la biblioteca propia (datos, expresiones, runtime)",
    )
    analizador.add_argument(
        "--sin-ventana",
        action="store_true",
        help=(
            "no abre visores externos para las gráficas (CI o demostración "
            "sin entorno gráfico); equivale a AREPA_SIN_VENTANA=1"
        ),
    )
    argumentos = analizador.parse_args()

    if argumentos.sin_ventana:
        os.environ["AREPA_SIN_VENTANA"] = "1"

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
            _mostrar_contexto(texto, e["linea"], e["columna"])
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
        return _ejecutar(arbol, texto)

    return 0


def _ejecutar(arbol, texto=""):
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
            "ErrorGrafica": "gráfico",
            "ErrorEjecucion": "ejecución",
            "ErrorArchivo": "ejecución",
            "ErrorCSV": "ejecución",
        }
        print("\nError de {0} durante la ejecución:".format(mapa.get(etiqueta, "ejecución")))
        print("  {0}".format(problema))
        if problema.contexto:
            print("  Contexto: {0}".format(problema.contexto))
        if problema.linea >= 0:
            _mostrar_contexto(texto, problema.linea, problema.columna)
        _resumen_archivos(ejecutor.contexto)
        print("\nUy, el programa se cayó. Corregí y volvé a intentar.")
        return 1
    except RetornoFuncion:
        _resumen_archivos(ejecutor.contexto)
        print("\nError semántico: 'devuelva' solo funciona dentro de una función.")
        return 1

    _resumen_archivos(ejecutor.contexto)
    print("\n¡De una! El programa corrió completo sin tropiezos.")
    return 0


def _silenciar_tuberia_rota():
    """Redirige fd 1 a /dev/null para que el cierre no vuelva a fallar.

    No basta con reasignar ``sys.stdout``: si el lector cerró la tubería
    mientras había datos en el búfer, el volcado final del intérprete
    vuelve a escribir en el descriptor original y termina con código 120.
    """
    try:
        sys.stdout.flush()
    except OSError:
        pass
    try:
        descriptor = os.open(os.devnull, os.O_WRONLY)
        os.dup2(descriptor, sys.stdout.fileno())
        os.close(descriptor)
    except (OSError, ValueError):
        sys.stdout = open(os.devnull, "w")


if __name__ == "__main__":
    try:
        codigo = main()
        try:
            # El volcado explícito convierte un EPIPE diferido (búfer
            # lleno y lector cerrado) en una salida limpia.
            sys.stdout.flush()
        except OSError:
            _silenciar_tuberia_rota()
            codigo = 0
        sys.exit(codigo)
    except BrokenPipeError:
        # Linux: el lector cerró la tubería (p. ej. `arepa demo.arepa --arbol
        # | head`): salir en silencio con código 0, sin volcado.
        _silenciar_tuberia_rota()
        sys.exit(0)
    except OSError as problema:
        # Linux: escribir en una tubería ya cerrada llega como EPIPE
        # (y en algunos kernels como EINVAL): se trata igual.
        import errno

        if problema.errno in (errno.EPIPE, errno.EINVAL):
            _silenciar_tuberia_rota()
            sys.exit(0)
        raise
