"""
AREPA - Manejo de errores del front-end (src/lenguaje/errores.py)
-----------------------------------------------------------------
Listener personalizado de ANTLR4 que captura los errores léxicos y
sintácticos sin interrumpir el análisis, los traduce a mensajes
comprensibles en español y conserva su ubicación (línea y columna).

La traducción de mensajes es código propio del equipo; la captura se
apoya en la interfaz de listeners de ANTLR4 (uso autorizado).
"""

import re

from antlr4.error.ErrorListener import ErrorListener


class ErroresArepa(ErrorListener):
    """Recolecta errores léxicos y sintácticos de un análisis."""

    LEXICO = "léxico"
    SINTACTICO = "sintáctico"

    # Límite de opciones a listar cuando ANTLR reporta muchas alternativas.
    MAX_OPCIONES = 6

    def __init__(self, tipo):
        super().__init__()
        self.tipo = tipo
        self.errores = []

    # ------------------------------------------------------------------ #
    def syntaxError(self, reconocedor, ofensivo, linea, columna, mensaje, e):
        self.errores.append(
            {
                "tipo": self.tipo,
                "linea": linea,
                "columna": columna,
                "mensaje": _traducir(mensaje),
                "detalle": mensaje,
            }
        )

    # ------------------------------------------------------------------ #
    def hay_errores(self):
        return len(self.errores) > 0

    def __len__(self):
        return len(self.errores)

    def resumen(self):
        """Devuelve las líneas de diagnóstico listas para mostrar."""
        lineas = []
        for e in self.errores:
            lineas.append(
                "[{0}] Línea {1}, Columna {2}: {3}".format(
                    e["tipo"], e["linea"], e["columna"], e["mensaje"]
                )
            )
        return lineas


# ---------------------------------------------------------------------- #
# Traducción de los mensajes técnicos de ANTLR a español claro
# ---------------------------------------------------------------------- #

# Nombres simbólicos de ANTLR y su lectura en español
NOMBRES_TOKEN = {
    "NL": "un salto de línea",
    "ID": "un identificador (nombre sin espacios)",
    "ENTERO": "un número entero",
    "DECIMAL": "un número decimal",
    "CADENA": "una cadena entre comillas dobles",
    "EOF": "el final del archivo",
}

# Palabras reservadas que un usuario puede intentar usar como variable
RESERVADAS = {
    "y": "el operador lógico 'y' (conjunción)",
    "o": "el operador lógico 'o' (disyunción)",
    "no": "el operador lógico 'no' (negación)",
    "obvio": "el literal verdadero 'obvio'",
    "falso": "el literal 'falso'",
    "nada": "el literal 'nada'",
}


def _primer_texto_entre_comillas(mensaje):
    inicio = mensaje.find("'")
    fin = mensaje.find("'", inicio + 1)
    if inicio != -1 and fin != -1:
        return mensaje[inicio : fin + 1]
    return None


def _limpiar_texto(texto):
    """Quita saltos de línea y espacios sobrantes de un fragmento citado."""
    if texto is None:
        return texto
    limpio = texto.replace("\\n", " ").replace("\\r", "").replace("\\t", " ")
    limpio = re.sub(r"\s+", " ", limpio).strip()
    limpio = limpio.strip("'").strip()
    if limpio == "":
        return "'(fin de línea)'"
    return "'" + limpio + "'"


def _traducir_token(token):
    """Convierte un elemento del conjunto esperado a lenguaje claro."""
    token = token.strip()
    if token == "":
        return token
    if token.startswith("'"):
        return token
    if token in NOMBRES_TOKEN:
        return NOMBRES_TOKEN[token]
    return "'" + token.lower() + "'"


def _traducir_conjunto(fragmento):
    """Recibe algo como {'chao', NL, ID} y devuelve una lista legible."""
    interior = fragmento.strip()
    if interior.startswith("{") and interior.endswith("}"):
        interior = interior[1:-1]
    opciones = [_traducir_token(t) for t in interior.split(",") if t.strip()]
    if len(opciones) > ErroresArepa.MAX_OPCIONES:
        visibles = opciones[: ErroresArepa.MAX_OPCIONES]
        return ", ".join(visibles) + ", entre otras opciones"
    return ", ".join(opciones)


def _pista_reservada(texto_crudo):
    """Si el usuario usó 'y', 'o', 'no', etc. como variable, lo explica."""
    if texto_crudo is None:
        return ""
    limpio = texto_crudo.strip("'").strip()
    primera = limpio.split()[0] if limpio.split() else ""
    if primera in RESERVADAS:
        return (
            " Ojo: {0} es una palabra reservada, no puede usarse como nombre"
            " de variable; escogé otro nombre.".format(RESERVADAS[primera])
        )
    return ""


def _traducir(mensaje):
    if mensaje.startswith("token recognition error"):
        simbolo = _primer_texto_entre_comillas(mensaje) or ""
        return "Hay un símbolo {0} que no hace parte del lenguaje AREPA".format(
            _limpiar_texto(simbolo)
        )

    if mensaje.startswith("missing"):
        partes = mensaje.split(" at ", 1)
        lo_que_falta = _traducir_conjunto(partes[0].replace("missing", ""))
        donde = _limpiar_texto(partes[1].strip()) if len(partes) > 1 else "allí"
        return "Hace falta {0} cerca de {1}".format(lo_que_falta, donde)

    if mensaje.startswith("extraneous input"):
        partes = mensaje.split(" expecting ", 1)
        crudo = _primer_texto_entre_comillas(partes[0])
        sobra = _limpiar_texto(crudo) or partes[0]
        esperaba = _traducir_conjunto(partes[1]) if len(partes) > 1 else ""
        pista = _pista_reservada(crudo)
        return "No esperaba {0} por ahí; revisá si sobra. En esa posición se esperaba {1}.{2}".format(
            sobra, esperaba, pista
        )

    if mensaje.startswith("mismatched input"):
        partes = mensaje.split(" expecting ", 1)
        crudo = _primer_texto_entre_comillas(partes[0])
        encontro = _limpiar_texto(crudo) or partes[0]
        esperaba = _traducir_conjunto(partes[1]) if len(partes) > 1 else ""
        pista = _pista_reservada(crudo)
        return "No esperaba {0} en esa posición; se esperaba {1}.{2}".format(
            encontro, esperaba, pista
        )

    if mensaje.startswith("no viable alternative"):
        crudo = _primer_texto_entre_comillas(mensaje)
        malo = _limpiar_texto(crudo)
        pista = _pista_reservada(crudo)
        return "Esa construcción {0} no cuadra con ninguna instrucción de AREPA.{1}".format(
            malo, pista
        ).replace("..", ".")

    if "expecting" in mensaje:
        partes = mensaje.split(" expecting ", 1)
        return "{0}; se esperaba {1}".format(
            _limpiar_texto(partes[0]).capitalize(),
            _traducir_conjunto(partes[1]) if len(partes) > 1 else "",
        )

    return mensaje.capitalize()
