"""
AREPA - REPL de consola con autocompletado por Tab (src/cli/repl.py)
--------------------------------------------------------------------
Consola interactiva para escribir AREPA con ayuda de completado,
sin salir de la terminal y sin dependencias nuevas (solo stdlib:
readline es parte de Python en Linux, exigido por el curso).

Uso:
    python3 src/cli/repl.py

Dentro:
    Tab              completa palabras reservadas y comandos
    :ayuda           muestra ayuda
    :ver             muestra lo escrito
    :validar         valida con el front-end (lexer+parser ANTLR)
    :limpiar         borra el buffer
    :guardar <ruta>  guarda el buffer como .arepa
    :salir           sale (Ctrl-D también sale)
"""

import os
import sys

_RUTA_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_SRC = os.path.dirname(_RUTA_AQUI)
_RAIZ_PROYECTO = os.path.abspath(os.path.join(_RUTA_AQUI, "..", ".."))
for _ruta in (_RAIZ_SRC, os.path.join(_RAIZ_PROYECTO, "generado")):
    _abs = os.path.abspath(_ruta)
    if _abs not in sys.path:
        sys.path.insert(0, _abs)

try:
    from lenguaje.analizador import analizar
except Exception:  # sin front-end no se puede validar, pero sí completar
    analizar = None

_DICT = os.path.join(_RAIZ_PROYECTO, "herramientas", "consola", "palabras_arepa.txt")
_FALLBACK = (
    "quihubo chao monte guarde como con encabezado separador escoja deje donde "
    "acomode por pa_arriba pa_abajo cree renombre limpie duplicados vacios convierta "
    "junte resuma numero texto logico fecha pinte barras lineas histograma dispersion "
    "cajas titulo ejex ejey leyenda guardela muestrela invente devuelva fijese_si sino "
    "cuenteme describa obvio falso nada y o no"
).split()

if os.path.isfile(_DICT):
    with open(_DICT, "r", encoding="utf-8") as fh:
        PALABRAS = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
else:
    PALABRAS = list(_FALLBACK)

COMANDOS = [":ayuda", ":ver", ":validar", ":limpiar", ":guardar", ":salir"]
TODO = sorted(set(PALABRAS + COMANDOS + ["|>", "->", "==", "!=", "<=", ">="]))


def _completar(texto, estado):
    """Función para readline: n-ésima coincidencia que empieza por texto."""
    if texto.startswith(":"):
        opciones = [c for c in COMANDOS if c.startswith(texto)]
    else:
        opciones = [p for p in TODO if p.startswith(texto)]
    if estado < len(opciones):
        return opciones[estado] + (" " if opciones[estado].startswith(":") else "")
    return None


def _activar_tab():
    try:
        import readline

        readline.set_completer(_completar)
        readline.parse_and_bind("tab: complete")
        hist = os.path.expanduser("~/.arepa_history")
        try:
            if os.path.isfile(hist):
                readline.read_history_file(hist)
        except Exception:
            pass
        import atexit

        atexit.register(lambda: _guardar_historial(hist))
        return True
    except Exception:
        return False


def _guardar_historial(hist):
    try:
        import readline

        readline.write_history_file(hist)
    except Exception:
        pass


def _envolver(buffer):
    """Envuelve en quihubo/chao si faltan, como exige la gramática."""
    txt = "\n".join(buffer).strip()
    if "quihubo" not in txt:
        txt = "quihubo\n" + txt
    if "chao" not in txt.split():
        txt = txt + "\nchao"
    return txt + "\n"


def main():
    con_tab = _activar_tab()
    print("AREPA interactivo. Tab completa ({0} palabras). Escribí :ayuda.".format(len(PALABRAS))
          + ("" if con_tab else " (Tab no disponible en este sistema)"))
    buffer = []
    while True:
        try:
            linea = input("arepa> ")
        except (EOFError, KeyboardInterrupt):
            print("\nChao.")
            break
        cmd = linea.strip()
        if cmd in (":salir", ":chao", "chao"):
            if cmd.startswith(":") or len(buffer) == 0:
                print("Chao.")
                break
            buffer.append(linea)
            continue
        if cmd == ":ayuda":
            print("Comandos: :ver :validar :limpiar :guardar <archivo> :salir. Tab completa.")
            continue
        if cmd == ":ver":
            print("\n".join(buffer) if buffer else "(vacío)")
            continue
        if cmd == ":limpiar":
            buffer = []
            print("Buffer limpio.")
            continue
        if cmd == ":validar":
            _validar(buffer)
            continue
        if cmd.startswith(":guardar"):
            partes = cmd.split(maxsplit=1)
            if len(partes) < 2:
                print("Uso: :guardar <archivo.arepa>")
            else:
                with open(partes[1], "w", encoding="utf-8") as fh:
                    fh.write(_envolver(buffer))
                print("Guardado en {0}.".format(partes[1]))
            continue
        if cmd.startswith(":"):
            print("Comando desconocido. :ayuda para ver la lista.")
            continue
        buffer.append(linea)

        # Validación rápida por línea: avisa si la palabra no existe.
        primera = linea.strip().split()
        if primera and primera[0] not in TODO and not primera[0].startswith(("#", '"')):
            suger = [p for p in PALABRAS if p.startswith(primera[0][:3])]
            if suger:
                print("  (¿quisiste decir: {0} ? Tab para completar)".format(", ".join(suger[:4])))


def _validar(buffer):
    if analizar is None:
        print("No se pudo cargar el front-end para validar.")
        return
    if not buffer:
        print("(vacío, nada que validar)")
        return
    _, _, errores = analizar(_envolver(buffer))
    if errores:
        print("Encontré {0} problema(s):".format(len(errores)))
        for e in errores:
            print("  [{0}] Línea {1}, Columna {2}: {3}".format(
                e["tipo"], e["linea"], e["columna"], e["mensaje"]))
    else:
        print("¡Quihubo pues! Programa bien escrito.")


if __name__ == "__main__":
    main()
