"""
AREPA - REPL de consola con autocompletado por Tab (src/cli/repl.py)
--------------------------------------------------------------------
Consola interactiva para escribir AREPA con ayuda de completado,
sin salir de la terminal y sin dependencias nuevas (solo stdlib).

En Linux (terminal real) muestra TEXTO FANTASMA: mientras escribes
aparece en gris lo que puedes completar y Tab (o FlechaDer) lo acepta.
Sin tty o con --simple usa el modo clásico con readline.

Uso:
    python3 src/cli/repl.py [--simple]

Dentro:
    Tab / FlechaDer  acepta el texto fantasma gris
    :ayuda           muestra ayuda
    :ver             muestra lo escrito
    :validar         valida con el front-end (lexer+parser ANTLR)
    :ejemplo [nombre] carga un ejemplo (demo, filtros, graficas, funciones)
    :plantilla <nombre> inserta un esqueleto (base, monte, tuberia, ...)
    :plantillas      lista los esqueletos disponibles
    :limpiar         borra el buffer
    :guardar <ruta>  guarda el buffer como .arepa (Tab completa archivos)
    :salir           sale (Ctrl-D también sale)
"""

import codecs
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import termios as _termios
    import tty as _tty
    _PUEDE_FANTASMA = True
except Exception:  # Windows u otros: sin modo fantasma, solo readline
    _termios = None
    _tty = None
    _PUEDE_FANTASMA = False
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
    "cuenteme describa mientras repita veces desde hasta paso pare siga "
    "obvio falso nada y o no"
).split()

if os.path.isfile(_DICT):
    with open(_DICT, "r", encoding="utf-8") as fh:
        PALABRAS = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
else:
    PALABRAS = list(_FALLBACK)

COMANDOS = [":ayuda", ":ver", ":validar", ":ejemplo", ":plantilla",
            ":plantillas", ":limpiar", ":guardar", ":salir"]
VOCABULARIO = sorted(set(PALABRAS + COMANDOS + ["|>", "->", "==", "!=", "<=", ">="]))

PLANTILLAS = {
    "base": ["quihubo", "", "", "chao"],
    "monte": ['datos = monte "datos/archivo.csv" con encabezado, separador ","'],
    "tuberia": ["resultado = datos",
                "|> escoja [col1, col2]",
                "|> deje donde col1 > 0",
                "|> cree total = col1 * col2"],
    "resumen": ["resumen = resultado",
                "|> junte por [col1]",
                "|> resuma total = sume(total), n = cuente()"],
    "pinte": ["pinte barras resumen",
              'titulo "Titulo"',
              "ejex col1",
              "ejey total",
              'guardela "salidas/grafica.png"'],
    "funcion": ["invente doble(x) {",
                "    devuelva x * 2",
                "}"],
    "fijese": ["fijese_si (x > 0) {",
               '    cuenteme "positivo"',
               "} sino {",
               '    cuenteme "cero o menos"',
               "}"],
    "ciclo": ["mientras (x > 0) {",
              "    x = x - 1",
              "}",
              "repita i desde 1 hasta 10 {",
              "    cuenteme i",
              "}"],
}

_EJEMPLOS = {"demo": "demo.arepa", "filtros": "filtros.arepa",
             "graficas": "graficas.arepa", "funciones": "funciones.arepa",
             "ciclos": "ciclos.arepa"}


def _archivos(texto):
    """Completa rutas para :guardar (solo .arepa y directorios)."""
    cands = glob.glob(texto + "*")
    sal = []
    for c in sorted(cands):
        if os.path.isdir(c):
            sal.append(c + os.sep)
        elif c.endswith(".arepa"):
            sal.append(c + " ")
    return sal


def _completar(texto, estado):
    """Función para readline: n-ésima coincidencia que empieza por texto."""
    try:
        import readline
        linea = readline.get_line_buffer()
    except Exception:
        linea = texto
    if linea.startswith(":guardar"):
        partes = linea.split(None, 1)
        frag = partes[1] if len(partes) > 1 else ""
        opciones = _archivos(frag)
    elif linea.startswith(":plantilla"):
        partes = linea.split(None, 1)
        frag = partes[1] if len(partes) > 1 else ""
        opciones = [p + " " for p in PLANTILLAS if p.startswith(frag)]
    elif linea.startswith(":ejemplo"):
        partes = linea.split(None, 1)
        frag = partes[1] if len(partes) > 1 else ""
        opciones = [e + " " for e in _EJEMPLOS if e.startswith(frag)]
    elif texto.startswith(":"):
        opciones = [c + " " for c in COMANDOS if c.startswith(texto)]
    else:
        opciones = [p for p in VOCABULARIO if p.startswith(texto)]
    if estado < len(opciones):
        return opciones[estado]
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


# --------------------------------------------------------------------
# Texto fantasma (modo raw, solo stdlib, Linux con tty)
# --------------------------------------------------------------------

def _sugerencia(linea, pos):
    """Texto que falta para completar la palabra bajo el cursor.

    Devuelve solo el sufijo (lo que se pinta en gris). "" si no hay.
    """
    i = pos
    while i > 0 and linea[i - 1] not in (" ", "\t"):
        i -= 1
    frag = linea[i:pos]
    if not frag:
        return ""
    if linea.startswith(":guardar"):
        cands = _archivos(frag)
        base = frag
    elif linea.startswith(":plantilla"):
        base = frag
        cands = [p + " " for p in PLANTILLAS if p.startswith(base)]
    elif linea.startswith(":ejemplo"):
        base = frag
        cands = [e + " " for e in _EJEMPLOS if e.startswith(base)]
    elif frag.startswith(":"):
        base = frag
        cands = [c + " " for c in COMANDOS if c.startswith(base)]
    else:
        base = frag.lstrip("[(,")  # ignora [(, pegados: "(fij" sugiere fijese_si
        cands = [p for p in VOCABULARIO if base and p.startswith(base)]
    for c in cands:
        if c.startswith(base) and len(c) > len(base):
            suf = c[len(base):]
            return suf if suf.strip() else ""
    return ""


def _pintar(prompt, buf, pos, fantasma):
    """Redibuja la línea: lo escrito + fantasma gris, cursor en su sitio."""
    texto = "".join(buf)
    sys.stdout.write("\r\x1b[K" + prompt + texto[:pos])
    resto = texto[pos:]
    sys.stdout.write(resto)
    ancho_fantasma = 0
    if fantasma and pos == len(buf):
        sys.stdout.write("\x1b[2m" + fantasma + "\x1b[0m")
        ancho_fantasma = len(fantasma)
    atraso = len(resto) + ancho_fantasma
    if atraso:
        sys.stdout.write("\x1b[{0}D".format(atraso))
    sys.stdout.flush()


def _leer_con_fantasma(prompt, historial):
    """Lee una línea mostrando el fantasma gris (Tab/FlechaDer lo acepta).

    Teclas: Enter envía, Tab/FlechaDer acepta, Retroceso borra,
    Flechas Arriba/Abajo/Izq/Der navegan, Ctrl-U limpia, Ctrl-C cancela,
    Ctrl-D sale si la línea está vacía.
    """
    fd = sys.stdin.fileno()
    viejo = _termios.tcgetattr(fd)
    dec = codecs.getincrementaldecoder("utf-8")()
    buf, pos = [], 0
    idx = len(historial)
    guardada = ""
    try:
        _tty.setraw(fd)
        while True:
            fantasma = _sugerencia("".join(buf), pos)
            _pintar(prompt, buf, pos, fantasma)
            b = os.read(fd, 1)
            if not b:
                return None
            ch = dec.decode(b)
            if ch == "":
                continue
            if ch in ("\r", "\n"):
                return "".join(buf)
            if ch == "\x03":  # Ctrl-C: cancela la línea
                sys.stdout.write("^C\r\n")
                buf, pos = [], 0
                continue
            if ch == "\x04":  # Ctrl-D: sale si no hay nada escrito
                if not buf:
                    return None
                continue
            if ch in ("\x7f", "\x08"):  # Retroceso
                if pos > 0:
                    del buf[pos - 1]
                    pos -= 1
                continue
            if ch == "\x15":  # Ctrl-U: limpia la línea
                buf, pos = [], 0
                continue
            if ch == "\t":  # Tab: acepta el fantasma
                if fantasma and pos == len(buf):
                    buf[pos:pos] = list(fantasma)
                    pos += len(fantasma)
                continue
            if ch == "\x1b":  # Secuencias de escape (flechas, Supr)
                s2 = dec.decode(os.read(fd, 1))
                s3 = dec.decode(os.read(fd, 1))
                if s2 == "[" and s3 == "3":  # Supr: \x1b[3~
                    dec.decode(os.read(fd, 1))
                    if pos < len(buf):
                        del buf[pos]
                elif s2 == "[" and s3 == "A":  # Arriba: historial
                    if idx > 0:
                        if idx == len(historial):
                            guardada = "".join(buf)
                        idx -= 1
                        buf = list(historial[idx])
                        pos = len(buf)
                elif s2 == "[" and s3 == "B":  # Abajo: historial
                    if idx < len(historial):
                        idx += 1
                        buf = list(historial[idx]) if idx < len(historial) else list(guardada)
                        pos = len(buf)
                elif s2 == "[" and s3 == "C":  # Der: mueve o acepta
                    if pos < len(buf):
                        pos += 1
                    elif fantasma:
                        buf[pos:pos] = list(fantasma)
                        pos += len(fantasma)
                elif s2 == "[" and s3 == "D":  # Izq
                    pos = max(0, pos - 1)
                continue
            if ch < " ":  # otros controles: se ignoran
                continue
            buf[pos:pos] = [ch]
            pos += 1
    finally:
        _termios.tcsetattr(fd, _termios.TCSADRAIN, viejo)
        sys.stdout.write("\r\n")
        sys.stdout.flush()


def _leer(prompt, historial, fantasma):
    """Lee una línea: fantasma si se puede, si no input() clásico."""
    if fantasma and _PUEDE_FANTASMA and sys.stdin.isatty():
        try:
            return _leer_con_fantasma(prompt, historial)
        except Exception:
            pass
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return None


def _envolver(buffer):
    """Envuelve en quihubo/chao si faltan, como exige la gramática."""
    txt = "\n".join(buffer).strip()
    if "quihubo" not in txt:
        txt = "quihubo\n" + txt
    if "chao" not in txt.split():
        txt = txt + "\nchao"
    return txt + "\n"


def main(argv=None):
    argv = list(argv) if argv is not None else []
    if "--help" in argv or "-h" in argv:
        print("Uso: python3 src/cli/repl.py [--simple] [--help]")
        print("Consola interactiva de AREPA con autocompletado por Tab.")
        print("  --simple   usa readline clásico (sin texto fantasma).")
        print("  --help     muestra esta ayuda.")
        print("Dentro: :ayuda :ver :validar :ejemplo [nombre] :plantilla <nombre>")
        print("        :plantillas :limpiar :guardar <archivo> :salir")
        return
    fantasma = ("--simple" not in argv)
    historial = []
    hist_path = os.path.expanduser("~/.arepa_history")
    if fantasma:
        try:
            if os.path.isfile(hist_path):
                with open(hist_path, "r", encoding="utf-8") as fh:
                    historial = [l.rstrip("\n") for l in fh][-200:]
        except Exception:
            pass
    else:
        con_tab = _activar_tab()
    if fantasma and _PUEDE_FANTASMA and sys.stdin.isatty():
        print("AREPA interactivo ({0} palabras). El texto gris es sugerencia: Tab la acepta.".format(len(PALABRAS)))
    elif not fantasma:
        print("AREPA interactivo. Tab completa ({0} palabras). Escribí :ayuda.".format(len(PALABRAS))
              + ("" if con_tab else " (Tab no disponible en este sistema)"))
    else:
        _activar_tab()
        print("AREPA interactivo. Tab completa ({0} palabras). Escribí :ayuda.".format(len(PALABRAS)))
    buffer = []
    while True:
        linea = _leer("arepa> ", historial, fantasma)
        if linea is None:
            print("\nChao.")
            break
        if fantasma and linea.strip():
            historial.append(linea)
            try:
                with open(hist_path, "a", encoding="utf-8") as fh:
                    fh.write(linea + "\n")
            except Exception:
                pass
        cmd = linea.strip()
        if cmd in (":salir", ":chao", "chao"):
            if cmd.startswith(":") or len(buffer) == 0:
                print("Chao.")
                break
            buffer.append(linea)
            continue
        if cmd == ":ayuda":
            print("Comandos: :ver :validar :ejemplo [nombre] :plantilla <nombre>")
            print("          :plantillas :limpiar :guardar <archivo> :salir.")
            print("Tab completa palabras, comandos, plantillas y archivos.")
            continue
        if cmd == ":plantillas":
            print("Plantillas: {0}. Uso: :plantilla <nombre>".format(
                ", ".join(sorted(PLANTILLAS))))
            continue
        if cmd.startswith(":plantilla"):
            partes = cmd.split(maxsplit=1)
            if len(partes) < 2 or partes[1] not in PLANTILLAS:
                print("Uso: :plantilla <nombre>. Disponibles: {0}".format(
                    ", ".join(sorted(PLANTILLAS))))
            else:
                buffer.extend(PLANTILLAS[partes[1]])
                print("Plantilla '{0}' insertada ({1} líneas).".format(
                    partes[1], len(PLANTILLAS[partes[1]])))
            continue
        if cmd.startswith(":ejemplo"):
            partes = cmd.split(maxsplit=1)
            nombre = partes[1] if len(partes) > 1 else "demo"
            if nombre not in _EJEMPLOS:
                print("Ejemplos: {0}. Uso: :ejemplo [nombre]".format(
                    ", ".join(sorted(_EJEMPLOS))))
            else:
                ruta = os.path.join(_RAIZ_PROYECTO, "ejemplos", _EJEMPLOS[nombre])
                with open(ruta, "r", encoding="utf-8") as fh:
                    buffer = [l.rstrip("\n") for l in fh]
                print("Ejemplo '{0}' cargado ({1} líneas). :ver para verlo.".format(
                    nombre, len(buffer)))
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
        if primera and primera[0] not in VOCABULARIO and not primera[0].startswith(("#", '"')):
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
    main(sys.argv[1:])
