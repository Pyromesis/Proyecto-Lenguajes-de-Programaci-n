"""
AREPA - Manejo de errores y diagnóstico (Fase 1)
------------------------------------------------
Listener personalizado de ANTLR4 que captura los errores léxicos y
sintácticos sin interrumpir el análisis, los traduce a mensajes
comprensibles en español y conserva su ubicación (línea y columna).
"""

from antlr4.error.ErrorListener import ErrorListener


class ErroresArepa(ErrorListener):
    """Recolecta errores léxicos y sintácticos de un análisis."""

    LEXICO = "léxico"
    SINTACTICO = "sintáctico"

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

def _primer_texto_entre_comillas(mensaje):
    inicio = mensaje.find("'")
    fin = mensaje.find("'", inicio + 1)
    if inicio != -1 and fin != -1:
        return mensaje[inicio : fin + 1]
    return None


def _traducir(mensaje):
    if mensaje.startswith("token recognition error"):
        simbolo = _primer_texto_entre_comillas(mensaje) or ""
        return (
            "Hay un símbolo {0} que no hace parte del lenguaje AREPA".format(simbolo)
        )

    if mensaje.startswith("missing"):
        partes = mensaje.split("at", 1)
        lo_que_falta = partes[0].replace("missing", "").strip()
        donde = partes[1].strip() if len(partes) > 1 else "allí"
        return "Hace falta {0} cerca de {1}".format(lo_que_falta, donde)

    if mensaje.startswith("extraneous input"):
        partes = mensaje.split("expecting", 1)
        sobra = _primer_texto_entre_comillas(partes[0]) or partes[0]
        esperaba = partes[1].strip() if len(partes) > 1 else ""
        return "No esperaba {0} por ahí; revisá si sobra. Se esperaba algo como {1}".format(
            sobra, esperaba
        )

    if mensaje.startswith("mismatched input"):
        partes = mensaje.split("expecting", 1)
        encontro = _primer_texto_entre_comillas(partes[0]) or partes[0]
        esperaba = partes[1].strip() if len(partes) > 1 else ""
        return "No esperaba {0} en esa posición; se esperaba {1}".format(encontro, esperaba)

    if mensaje.startswith("no viable alternative"):
        malo = _primer_texto_entre_comillas(mensaje)
        return "Esa construcción {0} no cuadra con ninguna instrucción de AREPA".format(
            malo or ""
        ).strip()

    if "expecting" in mensaje:
        partes = mensaje.split("expecting", 1)
        return "{0}; se esperaba {1}".format(
            partes[0].strip().capitalize(), partes[1].strip()
        )

    return mensaje.capitalize()
