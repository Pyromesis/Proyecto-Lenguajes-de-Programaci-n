"""
AREPA - Fuente bitmap 5x7 propia (src/graficas/fuente.py)
---------------------------------------------------------
Implementada por el equipo. Todo el texto de las gráficas se dibuja con
esta fuente de mapa de bits: no se usan fuentes del sistema ni
bibliotecas externas.

Qué hace:
  * define GLIFOS: un glifo por cada carácter ASCII imprimible (32..126),
    con 7 filas de 5 bits (el bit 4 es la columna izquierda);
  * normaliza el texto a ASCII imprimible con unicodedata (NFD) para
    quitar tildes y diéresis, y con un mapa propio para los signos que
    no se descomponen (¿, ¡, rayas, comillas tipográficas, ...);
  * mide cadenas (ancho_texto / alto_texto) con separación de 1 píxel
    entre caracteres, que es la misma que usa el lienzo al dibujar.

Decisiones propias documentadas:
  * el glifo de reemplazo es '?' y se usa para cualquier carácter no
    representable: así una etiqueta con emojis nunca rompe el dibujo;
  * la ñ se resuelve sola con NFD (n + tilde combinada); el resto de
    letras acentuadas sigue el mismo camino;
  * las minúsculas ocupan las cinco filas inferiores (altura de x) para
    que se distingan de las mayúsculas, que ocupan las siete;
  * la escala es un entero positivo: cada píxel del glifo se convierte
    en un bloque de escala x escala píxeles.

Limitaciones:
  * no hay descendentes reales (g, p, q, y, j) por la altura fija de 7
    filas: se dibujan dentro de la caja, algo comprimidas;
  * no se rotan textos: las etiquetas largas se recortan con "...".
"""

import unicodedata

# ---------------------------------------------------------------------- #
# Medidas de la fuente
# ---------------------------------------------------------------------- #

ANCHO = 5
ALTO = 7
SEPARACION = 1

CARACTER_REEMPLAZO = "?"

# ---------------------------------------------------------------------- #
# Mapa de caracteres que NFD no descompone en ASCII
# ---------------------------------------------------------------------- #

_ESPECIALES = {
    "¿": "?",
    "¡": "!",
    "–": "-",
    "—": "-",
    "‒": "-",
    "―": "-",
    "−": "-",
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
    "′": "'",
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "″": '"',
    "…": "...",
    "•": "*",
    "·": ".",
    "×": "x",
    "÷": "/",
    "°": "o",
    "\t": "    ",
    "\r": "",
    "\u00a0": " ",  # espacio duro
    "\u2009": " ",  # espacio fino
    "\u202f": " ",  # espacio fino sin salto
}

# ---------------------------------------------------------------------- #
# Tabla de glifos: 7 filas de 5 bits por carácter
# ---------------------------------------------------------------------- #

# Cada entrada es una cadena con las 7 filas separadas por espacios.
# El bit 4 (0b10000) es la columna izquierda y el bit 0 la derecha.
_FILAS = {
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    '"': "01010 01010 00000 00000 00000 00000 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "$": "00100 01111 10100 01110 00101 11110 00100",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "'": "00100 00100 00000 00000 00000 00000 00000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "*": "00000 00100 10101 01110 10101 00100 00000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    ",": "00000 00000 00000 00000 00110 00100 01000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 00110 00110",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    ":": "00000 00110 00110 00000 00110 00110 00000",
    ";": "00000 00110 00110 00000 00110 00100 01000",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    "@": "01110 10001 00001 01101 10101 10101 01110",
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11100 10010 10001 10001 10001 10010 11100",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "[": "01110 01000 01000 01000 01000 01000 01110",
    "\\": "10000 01000 01000 00100 00010 00010 00001",
    "]": "01110 00010 00010 00010 00010 00010 01110",
    "^": "00100 01010 10001 00000 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "`": "01000 00100 00000 00000 00000 00000 00000",
    "a": "00000 00000 01110 00001 01111 10001 01111",
    "b": "10000 10000 11110 10001 10001 10001 11110",
    "c": "00000 00000 01110 10001 10000 10001 01110",
    "d": "00001 00001 01111 10001 10001 10001 01111",
    "e": "00000 00000 01110 10001 11111 10000 01110",
    "f": "00110 01001 01000 11100 01000 01000 01000",
    "g": "00000 00000 01110 10001 01111 00001 01110",
    "h": "10000 10000 11110 10001 10001 10001 10001",
    "i": "00100 00000 01100 00100 00100 00100 01110",
    "j": "00010 00000 00110 00010 00010 10010 01100",
    "k": "10000 10000 10010 10100 11000 10100 10010",
    "l": "01100 00100 00100 00100 00100 00100 01110",
    "m": "00000 00000 11010 10101 10101 10101 10101",
    "n": "00000 00000 11110 10001 10001 10001 10001",
    "o": "00000 00000 01110 10001 10001 10001 01110",
    "p": "00000 00000 11110 10001 11110 10000 10000",
    "q": "00000 00000 01111 10001 01111 00001 00001",
    "r": "00000 00000 10110 11001 10000 10000 10000",
    "s": "00000 00000 01111 10000 01110 00001 11110",
    "t": "01000 01000 11100 01000 01000 01001 00110",
    "u": "00000 00000 10001 10001 10001 10011 01101",
    "v": "00000 00000 10001 10001 10001 01010 00100",
    "w": "00000 00000 10001 10001 10101 10101 01010",
    "x": "00000 00000 10001 01010 00100 01010 10001",
    "y": "00000 00000 10001 10001 01111 00001 01110",
    "z": "00000 00000 11111 00010 00100 01000 11111",
    "{": "00110 00100 00100 01000 00100 00100 00110",
    "|": "00100 00100 00100 00100 00100 00100 00100",
    "}": "01100 00100 00100 00010 00100 00100 01100",
    "~": "00000 00000 01001 10110 00000 00000 00000",
}

GLIFOS = {
    ord(caracter): tuple(int(fila, 2) for fila in filas.split())
    for caracter, filas in _FILAS.items()
}

GLIFO_DESCONOCIDO = GLIFOS[ord(CARACTER_REEMPLAZO)]


def _verificar_tabla():
    """Comprueba al importar que la tabla cubre el ASCII imprimible."""
    faltantes = [chr(c) for c in range(32, 127) if c not in GLIFOS]
    if faltantes:
        raise RuntimeError(
            "faltan glifos para: {0!r}".format("".join(faltantes))
        )
    for codigo, filas_glifo in GLIFOS.items():
        if len(filas_glifo) != ALTO:
            raise RuntimeError(
                "el glifo {0!r} no tiene {1} filas".format(chr(codigo), ALTO)
            )
        for fila in filas_glifo:
            if not 0 <= fila < (1 << ANCHO):
                raise RuntimeError(
                    "el glifo {0!r} tiene una fila de más de {1} bits".format(
                        chr(codigo), ANCHO
                    )
                )


_verificar_tabla()


# ---------------------------------------------------------------------- #
# Normalización de texto
# ---------------------------------------------------------------------- #

def normalizar_texto(texto):
    """Convierte 'texto' a ASCII imprimible dibujable.

    Descompone con NFD para quitar tildes y diéresis (á -> a, ü -> u,
    ñ -> n), traduce los signos que no se descomponen (¿, ¡, rayas,
    comillas tipográficas, ...) y sustituye por '?' lo que no se pueda
    representar. Los saltos de línea se conservan.
    """
    if texto is None:
        return ""
    if not isinstance(texto, str):
        texto = str(texto)

    salida = []
    for caracter in unicodedata.normalize("NFD", texto):
        if unicodedata.combining(caracter):
            continue  # tilde o diéresis ya separada de su letra
        if caracter == "\n":
            salida.append(caracter)
            continue
        especial = _ESPECIALES.get(caracter)
        if especial is not None:
            salida.append(especial)
            continue
        codigo = ord(caracter)
        if 32 <= codigo <= 126:
            salida.append(caracter)
        else:
            salida.append(CARACTER_REEMPLAZO)
    return "".join(salida)


def _validar_escala(escala):
    """Exige una escala entera mayor que cero."""
    if isinstance(escala, bool) or not isinstance(escala, int):
        raise ValueError(
            "'escala' debe ser un entero; recibí {0}.".format(repr(escala))
        )
    if escala < 1:
        raise ValueError(
            "'escala' debe ser mayor que cero; recibí {0}.".format(escala)
        )
    return escala


# ---------------------------------------------------------------------- #
# Consulta de glifos y medidas
# ---------------------------------------------------------------------- #

def filas(caracter):
    """Devuelve las 7 filas de 5 bits del glifo de 'caracter'.

    El carácter se normaliza antes de buscarlo; si no es representable
    se devuelve el glifo de '?'. Se lanza ValueError si no es un único
    carácter.
    """
    if not isinstance(caracter, str) or len(caracter) != 1:
        raise ValueError(
            "'caracter' debe ser una cadena de un solo carácter; "
            "recibí {0!r}.".format(caracter)
        )
    normalizado = normalizar_texto(caracter)
    if len(normalizado) != 1:
        return GLIFO_DESCONOCIDO
    return GLIFOS.get(ord(normalizado), GLIFO_DESCONOCIDO)


def ancho_texto(texto, escala=1):
    """Ancho en píxeles de 'texto' con la separación entre caracteres.

    Con varias líneas devuelve el ancho de la más larga.
    """
    escala = _validar_escala(escala)
    maximo = 0
    for linea in normalizar_texto(texto).split("\n"):
        if not linea:
            continue
        ancho = len(linea) * ANCHO * escala + (len(linea) - 1) * SEPARACION * escala
        if ancho > maximo:
            maximo = ancho
    return maximo


def alto_texto(escala=1):
    """Alto en píxeles de una línea de texto."""
    return ALTO * _validar_escala(escala)
