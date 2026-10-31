"""
AREPA - Lienzo RGB propio (src/graficas/lienzo.py)
--------------------------------------------------
Implementado por el equipo. Superficie de dibujo en memoria sobre la que
se construyen las gráficas: un búfer bytearray RGB de 8 bits por canal
y un conjunto pequeño de primitivas rasterizadas a mano.

Qué hace:
  * pinta píxeles, líneas (Bresenham), rectángulos, círculos rellenos y
    texto con la fuente bitmap propia;
  * recorta cualquier trazo contra los bordes: nunca lanza IndexError;
  * valida los colores como tuplas (r, g, b) con canales 0..255;
  * entrega el búfer como bytes y lo codifica a PNG con png.py.

Decisiones propias documentadas:
  * el fondo por defecto es blanco (255, 255, 255), igual que el de las
    gráficas;
  * el grosor de una línea se implementa con un sello cuadrado de
    grosor x grosor píxeles centrado en cada punto de Bresenham;
  * el círculo relleno se dibuja por filas con math.isqrt, sin coma
    flotante y sin acumular error;
  * los rellenos escriben por franjas con asignación de slices, que en
    Python puro es bastante más rápido que píxel a píxel;
  * 'poner' fuera del lienzo se ignora en silencio (recorte seguro);
  * el texto avanza 5*escala píxeles por glifo más 1*escala de
    separación, y 9*escala entre líneas.

Limitaciones:
  * no hay antialiasing: los bordes son duros, a propósito, para que el
    PNG sea pequeño y el resultado sea reproducible;
  * no se implementan rotaciones ni transparencias.
"""

import math

from graficas import png
from graficas.fuente import (
    ALTO,
    ANCHO,
    SEPARACION,
    alto_texto as alto_texto_fuente,
    ancho_texto as ancho_texto_fuente,
    filas as filas_glifo,
    normalizar_texto,
)

COLOR_FONDO = (255, 255, 255)

_AVANCE_GLIFO = ANCHO + SEPARACION
_ALTO_LINEA = ALTO + 2


# ---------------------------------------------------------------------- #
# Validaciones
# ---------------------------------------------------------------------- #

def normalizar_color(color):
    """Devuelve el color como tupla (r, g, b) validada.

    Acepta tuplas o listas de tres enteros entre 0 y 255. Cualquier otro
    valor lanza ValueError para no pintar colores silenciosamente raros.
    """
    if not isinstance(color, (tuple, list)) or len(color) != 3:
        raise ValueError(
            "el color debe ser una tupla (r, g, b); recibí {0!r}.".format(color)
        )
    canales = []
    for canal in color:
        if isinstance(canal, bool) or not isinstance(canal, int):
            raise ValueError(
                "cada canal del color debe ser un entero; recibí {0!r}.".format(canal)
            )
        if not 0 <= canal <= 255:
            raise ValueError(
                "cada canal del color debe estar entre 0 y 255; recibí {0}.".format(
                    canal
                )
            )
        canales.append(canal)
    return (canales[0], canales[1], canales[2])


def _validar_entero_positivo(valor, nombre):
    """Exige un entero (sin bool) mayor que cero."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(
            "'{0}' debe ser un entero; recibí {1!r}.".format(nombre, valor)
        )
    if valor < 1:
        raise ValueError(
            "'{0}' debe ser mayor que cero; recibí {1}.".format(nombre, valor)
        )
    return valor


# ---------------------------------------------------------------------- #
# Lienzo
# ---------------------------------------------------------------------- #

class Lienzo:
    """Búfer RGB con primitivas de dibujo recortadas a sus bordes."""

    __slots__ = ("ancho", "alto", "color_fondo", "_buf")

    def __init__(self, ancho, alto, fondo=COLOR_FONDO):
        self.ancho = _validar_entero_positivo(ancho, "ancho")
        self.alto = _validar_entero_positivo(alto, "alto")
        self.color_fondo = normalizar_color(fondo)
        self._buf = bytearray(bytes(self.color_fondo) * (self.ancho * self.alto))

    # ------------------------------ utilidades ----------------------- #

    def _byte_color(self, color):
        """Color ya validado a bytes, listo para asignar por franjas."""
        return bytes(color)

    def _rellenar(self, x, y, ancho, alto, rgb):
        """Pinta un rectángulo de color 'rgb' (bytes) con recorte seguro."""
        if ancho <= 0 or alto <= 0:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.ancho, x + ancho)
        y1 = min(self.alto, y + alto)
        if x0 >= x1 or y0 >= y1:
            return
        trozo = rgb * (x1 - x0)
        longitud = len(trozo)
        for fila in range(y0, y1):
            inicio = (fila * self.ancho + x0) * 3
            self._buf[inicio:inicio + longitud] = trozo

    def _poner(self, x, y, rgb):
        """Pinta un píxel sin validar (x, y ya son enteros)."""
        if 0 <= x < self.ancho and 0 <= y < self.alto:
            inicio = (y * self.ancho + x) * 3
            self._buf[inicio:inicio + 3] = rgb

    def _sello(self, x, y, rgb, grosor):
        """Pinta el sello cuadrado de una línea de grosor > 1."""
        if grosor == 1:
            self._poner(x, y, rgb)
            return
        inicio = -(grosor // 2)
        self._rellenar(x + inicio, y + inicio, grosor, grosor, rgb)

    # ------------------------------ píxeles -------------------------- #

    def poner(self, x, y, color):
        """Pinta el píxel (x, y); fuera del lienzo no hace nada."""
        rgb = self._byte_color(normalizar_color(color))
        if isinstance(x, bool) or isinstance(y, bool):
            return
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("las coordenadas deben ser enteros.")
        self._poner(x, y, rgb)

    # ------------------------------ líneas --------------------------- #

    def linea(self, x0, y0, x1, y1, color, grosor=1):
        """Línea de (x0, y0) a (x1, y1) con el algoritmo de Bresenham.

        'grosor' es el lado del sello cuadrado que se estampa en cada
        punto; con 1 se obtiene una línea de un píxel.
        """
        rgb = self._byte_color(normalizar_color(color))
        grosor = _validar_entero_positivo(grosor, "grosor")
        if not all(isinstance(v, int) and not isinstance(v, bool)
                   for v in (x0, y0, x1, y1)):
            raise ValueError("las coordenadas de la línea deben ser enteros.")

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        paso_x = 1 if x0 < x1 else -1
        paso_y = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self._sello(x0, y0, rgb, grosor)
            if x0 == x1 and y0 == y1:
                break
            doble = 2 * error
            if doble >= dy:
                error += dy
                x0 += paso_x
            if doble <= dx:
                error += dx
                y0 += paso_y

    # --------------------------- rectángulos ------------------------- #

    def rectangulo(self, x, y, ancho, alto, color, grosor=1):
        """Contorno de un rectángulo; con tamaño nulo no dibuja nada."""
        rgb = self._byte_color(normalizar_color(color))
        grosor = _validar_entero_positivo(grosor, "grosor")
        if ancho <= 0 or alto <= 0:
            return
        self._rellenar(x, y, ancho, grosor, rgb)
        self._rellenar(x, y + alto - grosor, ancho, grosor, rgb)
        self._rellenar(x, y, grosor, alto, rgb)
        self._rellenar(x + ancho - grosor, y, grosor, alto, rgb)

    def rectangulo_relleno(self, x, y, ancho, alto, color):
        """Rectángulo macizo; con tamaño nulo no dibuja nada."""
        rgb = self._byte_color(normalizar_color(color))
        self._rellenar(x, y, ancho, alto, rgb)

    # ----------------------------- círculos -------------------------- #

    def circulo_relleno(self, cx, cy, radio, color):
        """Círculo macizo por filas, con recorte en los bordes."""
        rgb = self._byte_color(normalizar_color(color))
        if isinstance(radio, bool) or not isinstance(radio, int):
            raise ValueError("'radio' debe ser un entero.")
        if radio < 0:
            raise ValueError("'radio' no puede ser negativo.")
        if not isinstance(cx, int) or not isinstance(cy, int):
            raise ValueError("el centro del círculo debe ser entero.")
        if radio == 0:
            self._poner(cx, cy, rgb)
            return
        cuadrado = radio * radio
        for desplazamiento in range(-radio, radio + 1):
            medio = math.isqrt(cuadrado - desplazamiento * desplazamiento)
            self._rellenar(
                cx - medio, cy + desplazamiento, 2 * medio + 1, 1, rgb
            )

    # ------------------------------ texto ---------------------------- #

    def _trazar_glifo(self, x, y, filas, rgb, escala):
        """Pinta un glifo de 5x7 ampliado por 'escala'."""
        for numero_fila, bits in enumerate(filas):
            if not bits:
                continue
            fila_y = y + numero_fila * escala
            columna = 0
            while columna < ANCHO:
                if bits & (1 << (ANCHO - 1 - columna)):
                    inicio = columna
                    while (
                        columna < ANCHO
                        and bits & (1 << (ANCHO - 1 - columna))
                    ):
                        columna += 1
                    self._rellenar(
                        x + inicio * escala,
                        fila_y,
                        (columna - inicio) * escala,
                        escala,
                        rgb,
                    )
                else:
                    columna += 1

    def texto(self, x, y, texto, color=(20, 20, 20), escala=1):
        """Escribe 'texto' con la fuente propia desde la esquina superior.

        Admite varias líneas separadas por '\\n'. Devuelve la coordenada
        y del píxel siguiente a la última línea dibujada.
        """
        rgb = self._byte_color(normalizar_color(color))
        escala = _validar_entero_positivo(escala, "escala")
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("las coordenadas del texto deben ser enteras.")

        cursor_y = y
        for linea in normalizar_texto(texto).split("\n"):
            cursor_x = x
            for caracter in linea:
                self._trazar_glifo(
                    cursor_x, cursor_y, filas_glifo(caracter), rgb, escala
                )
                cursor_x += _AVANCE_GLIFO * escala
            cursor_y += _ALTO_LINEA * escala
        return cursor_y

    def ancho_texto(self, texto, escala=1):
        """Ancho en píxeles que ocupará 'texto' (la línea más larga)."""
        return ancho_texto_fuente(texto, escala)

    def alto_texto(self, escala=1):
        """Alto en píxeles de una línea de texto."""
        return alto_texto_fuente(escala)

    # ------------------------------ salida --------------------------- #

    def pixeles(self):
        """Búfer RGB inmutable, en orden de filas."""
        return bytes(self._buf)

    def png(self, compresion="fijo"):
        """Codifica el lienzo como PNG (bytes)."""
        return png.codificar_png(
            self.ancho, self.alto, self.pixeles(), compresion
        )

    def guardar(self, ruta, compresion="fijo"):
        """Guarda el lienzo en 'ruta' y devuelve el tamaño del archivo."""
        return png.escribir_png(
            ruta, self.ancho, self.alto, self.pixeles(), compresion
        )
