"""
AREPA - Tipos de gráfica y motor de dibujo (src/graficas/tipos_grafica.py)
-------------------------------------------------------------------------
Implementado por el equipo. Construye las cinco gráficas del DSL sobre
el Lienzo propio y la fuente bitmap propia, sin dependencias externas.

Qué hace:
  * define Serie y Grafica, y la función de conveniencia dibujar();
  * implementa barras, líneas, histograma, dispersión y cajas;
  * comparte el marco: márgenes fijos, título centrado, nombre de los
    ejes, rejilla horizontal suave, ejes grises, ticks con etiquetas y
    leyenda arriba a la derecha cuando hace falta;
  * expone cuartiles() y cubetas_histograma() como funciones públicas
    para que las pruebas verifiquen la estadística sin mirar píxeles.

Decisiones propias documentadas:
  * paleta de ocho colores distinguibles, asignada por orden de serie;
  * en barras, las categorías repetidas se SUMAN y se documenta aquí:
    es el comportamiento natural para datos agrupados;
  * el histograma usa solo la primera serie y cubetas de igual ancho
    (5 a 20, según sqrt(n)); las barras van contiguas;
  * los cuartiles se interpolan por posición (Q1, Q2, Q3), los bigotes
    son 1.5 * IQR recortados a los datos y los valores fuera se dibujan
    como puntos atípicos;
  * valores None, "nada", cadenas vacías, NaN e infinito se ignoran;
  * las etiquetas categóricas se recortan con "..." y nunca se rotan;
  * el dominio numérico se extiende hasta múltiplos del paso "bonito"
    para que la rejilla y los ticks coincidan con los bordes del área.

Limitaciones:
  * no hay subtítulos, eje secundario ni gráficas apiladas;
  * en cajas, si los valores de x se repiten (texto o número) se agrupa
    una caja por valor; si cada x es única, hay una caja por serie;
  * el texto se dibuja horizontal: etiquetas muy largas se recortan.
"""

import math

from graficas.escalas import (
    EscalaBanda,
    EscalaLineal,
    formatear,
    paso_bonito,
)
from graficas.fuente import (
    ancho_texto as ancho_texto_fuente,
)
from graficas.lienzo import Lienzo

# ---------------------------------------------------------------------- #
# Constantes de presentación
# ---------------------------------------------------------------------- #

TIPOS = ("barras", "lineas", "histograma", "dispersion", "cajas")

PALETA = (
    (31, 119, 180),    # azul
    (255, 127, 14),    # naranja
    (44, 160, 44),     # verde
    (214, 39, 40),     # rojo
    (148, 103, 189),   # morado
    (140, 86, 75),     # marrón
    (227, 119, 194),   # rosa
    (127, 127, 127),   # gris
)

MARGEN_IZQUIERDO = 78
MARGEN_DERECHO = 24
MARGEN_SUPERIOR = 64
MARGEN_INFERIOR = 64

_TEXTO = (55, 55, 55)
_TITULO = (20, 20, 20)
_EJE = (95, 95, 95)
_REJILLA = (228, 228, 228)
_BLANCO = (255, 255, 255)

_MENSAJE_SIN_DATOS = "La gráfica no tiene datos numéricos para dibujar."


# ---------------------------------------------------------------------- #
# Utilidades de datos
# ---------------------------------------------------------------------- #

def _sin_datos():
    """Error uniforme para una gráfica sin valores representables."""
    return ValueError(_MENSAJE_SIN_DATOS)


def _numero(valor):
    """Convierte a float finito; devuelve None para vacíos, 'nada' y NaN."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return float(valor)
    if isinstance(valor, (int, float)):
        numero = float(valor)
        return numero if math.isfinite(numero) else None
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto or texto.lower() == "nada":
            return None
        try:
            numero = float(texto)
        except ValueError:
            return None
        return numero if math.isfinite(numero) else None
    return None


def _clave_categoria(categoria):
    """Clave normalizada para agrupar categorías (número o texto)."""
    numero = _numero(categoria)
    if numero is not None:
        return ("n", numero)
    if categoria is None:
        return ("s", "nada")
    texto = str(categoria).strip()
    return ("s", texto if texto else "nada")


def _etiqueta_categoria(categoria):
    """Texto visible de una categoría, sin notación innecesaria."""
    numero = _numero(categoria)
    if numero is not None:
        return formatear(numero)
    if categoria is None:
        return "nada"
    texto = str(categoria).strip()
    return texto if texto else "nada"


def _limites(valores, incluir_cero=False, cantidad=5):
    """Extiende (min, max) hasta múltiplos del paso bonito del eje."""
    valores = list(valores)
    if not valores:
        raise _sin_datos()
    minimo = min(valores)
    maximo = max(valores)
    if incluir_cero:
        minimo = min(minimo, 0.0)
        maximo = max(maximo, 0.0)
    if minimo == maximo:
        delta = abs(minimo) * 0.1 if minimo != 0 else 1.0
        minimo -= delta
        maximo += delta

    paso = paso_bonito(maximo - minimo, cantidad)
    bajo = math.floor(minimo / paso + 1e-9) * paso
    alto = math.ceil(maximo / paso - 1e-9) * paso
    if bajo == alto:
        alto = bajo + paso
    return round(bajo, 10), round(alto, 10)


def _recortar(texto, maximo, escala=1):
    """Recorta 'texto' con '...' para que quepa en 'maximo' píxeles."""
    texto = "" if texto is None else str(texto)
    if maximo <= 0:
        return ""
    if ancho_texto_fuente(texto, escala) <= maximo:
        return texto
    puntos = "..."
    if ancho_texto_fuente(puntos, escala) > maximo:
        return ""
    recorte = texto
    while recorte and ancho_texto_fuente(recorte + puntos, escala) > maximo:
        recorte = recorte[:-1]
    return (recorte.rstrip() + puntos) if recorte else ""


# Separación mínima, en píxeles, entre dos etiquetas del eje x.
_SEPARACION_MINIMA_ETIQUETAS = 8


def _fecha_iso_corta(texto):
    """Devuelve 'MM-DD' si 'texto' es una fecha ISO 'AAAA-MM-DD'."""
    if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
        return None
    if not (texto[:4].isdigit() and texto[5:7].isdigit() and texto[8:].isdigit()):
        return None
    return texto[5:]


def _acortar_etiqueta(texto, ancho_area):
    """Acorta una etiqueta solo si no cabe ni en todo el área de trazado.

    Las fechas ISO prefieren su forma corta (MM-DD) antes de perder
    información con "..."; cualquier otro texto se recorta con puntos
    suspensivos. Si cabe completa se devuelve intacta.
    """
    texto = "" if texto is None else str(texto)
    if ancho_texto_fuente(texto) <= ancho_area:
        return texto
    corta = _fecha_iso_corta(texto)
    if corta is not None and ancho_texto_fuente(corta) <= ancho_area:
        return corta
    return _recortar(texto, ancho_area)


def _seleccionar_etiquetas(posiciones, etiquetas, max_ancho):
    """Elige los índices de las etiquetas que se dibujan en el eje x.

    Si todas las etiquetas completas caben entre centros (y ninguna es
    más ancha que el espacio disponible 'max_ancho'), devuelve todas,
    que es el comportamiento histórico. Si no, se queda con una de cada
    k = ceil((ancho_etiqueta + separación) / espacio_entre_centros),
    empezando por la primera y procurando incluir la última si hay sitio.
    Las etiquetas no se recortan aquí: eso solo ocurre cuando una
    etiqueta es más ancha que el área completa de trazado.
    """
    total = min(len(posiciones), len(etiquetas))
    if total <= 1:
        return list(range(total))
    posiciones = [float(posicion) for posicion in posiciones[:total]]
    etiquetas = ["" if etiqueta is None else str(etiqueta)
                 for etiqueta in etiquetas[:total]]
    anchos = [ancho_texto_fuente(etiqueta) for etiqueta in etiquetas]
    huecos = [
        posiciones[indice + 1] - posiciones[indice]
        for indice in range(total - 1)
    ]
    hueco_minimo = min(huecos)
    if hueco_minimo <= 0:
        return [0]

    margen = _SEPARACION_MINIMA_ETIQUETAS
    # ¿Caben todas? Se exige que dos etiquetas vecinas no se toquen
    # (cada una ocupa la mitad de su ancho desde su centro) y que
    # ninguna exceda el espacio disponible de su banda.
    if (
        max(anchos) <= max(1, int(max_ancho))
        and all(
            huecos[indice]
            >= (anchos[indice] + anchos[indice + 1]) / 2.0 + margen
            for indice in range(total - 1)
        )
    ):
        return list(range(total))

    ancho_etiqueta = max(anchos)
    salto = max(
        2,
        int(math.ceil((ancho_etiqueta + margen) / hueco_minimo)),
    )
    indices = list(range(0, total, salto))

    ultimo = total - 1
    if indices[-1] != ultimo:
        # Se intenta añadir la última; si no entra tras la anterior, se
        # sustituye la anterior por la última cuando el hueco lo permite.
        if posiciones[ultimo] - posiciones[indices[-1]] >= anchos[ultimo] + margen:
            indices.append(ultimo)
        elif len(indices) >= 2:
            previo = indices[-2]
            if posiciones[ultimo] - posiciones[previo] >= (
                max(anchos[previo], anchos[ultimo]) + margen
            ):
                indices[-1] = ultimo
    return indices


def _aclarar(color, factor):
    """Mezcla 'color' con blanco: factor 0 deja el color, 1 lo blanquea."""
    return tuple(
        int(round(canal + (255 - canal) * factor)) for canal in color
    )


# ---------------------------------------------------------------------- #
# Serie
# ---------------------------------------------------------------------- #

class Serie:
    """Una serie de datos: nombre, valores x (opcionales) y valores y.

    'x' puede ser numérica o textual; si se omite se usa el índice de
    cada valor. 'x' e 'y' deben tener la misma longitud.
    """

    __slots__ = ("nombre", "x", "y")

    def __init__(self, nombre, x, y):
        if y is None:
            raise ValueError(
                "La serie {0!r} necesita una lista de valores y.".format(nombre)
            )
        self.nombre = "" if nombre is None else str(nombre)
        self.y = list(y)
        if x is None:
            self.x = None
        else:
            self.x = list(x)
            if len(self.x) != len(self.y):
                raise ValueError(
                    "La serie {0!r} tiene {1} valores x y {2} valores y; "
                    "deben coincidir.".format(
                        self.nombre, len(self.x), len(self.y)
                    )
                )

    def __repr__(self):
        return "Serie({0!r}, {1} puntos)".format(self.nombre, len(self.y))


# ---------------------------------------------------------------------- #
# Estadística propia
# ---------------------------------------------------------------------- #

def _cuantil(ordenados, proporcion):
    """Cuantil por interpolación lineal entre posiciones vecinas."""
    if len(ordenados) == 1:
        return float(ordenados[0])
    posicion = (len(ordenados) - 1) * proporcion
    inferior = int(math.floor(posicion))
    superior = int(math.ceil(posicion))
    if inferior == superior:
        return float(ordenados[inferior])
    peso = posicion - inferior
    return float(
        ordenados[inferior]
        + (ordenados[superior] - ordenados[inferior]) * peso
    )


def cuartiles(valores):
    """Devuelve (Q1, Q2, Q3) con interpolación lineal por posición.

    Es el método "linear" habitual: con datos [1, 2, 3, 4, 5] da
    (2.0, 3.0, 4.0) y con [1, 2, 3, 4] da (1.75, 2.5, 3.25).
    Los valores vacíos y no numéricos se descartan.
    """
    numeros = sorted(
        numero for numero in (_numero(valor) for valor in valores)
        if numero is not None
    )
    if not numeros:
        raise ValueError("No hay valores numéricos para calcular cuartiles.")
    return (
        _cuantil(numeros, 0.25),
        _cuantil(numeros, 0.5),
        _cuantil(numeros, 0.75),
    )


def cantidad_cubetas(total):
    """Número de cubetas automático: 5 a 20, según ceil(sqrt(n))."""
    if isinstance(total, bool) or not isinstance(total, int):
        raise ValueError("'total' debe ser un entero.")
    if total < 1:
        raise ValueError("'total' debe ser mayor que cero.")
    return max(5, min(20, int(math.ceil(math.sqrt(total)))))


def cubetas_histograma(valores, cantidad=None):
    """Calcula bordes y conteos de un histograma de cubetas iguales.

    Devuelve (bordes, conteos): hay len(conteos) cubetas y len(bordes)
    es len(conteos) + 1. Con 'cantidad' en None se usa cantidad_cubetas.
    """
    numeros = [
        numero for numero in (_numero(valor) for valor in valores)
        if numero is not None
    ]
    if not numeros:
        raise ValueError("No hay valores numéricos para el histograma.")
    if cantidad is None:
        cantidad = cantidad_cubetas(len(numeros))
    elif isinstance(cantidad, bool) or not isinstance(cantidad, int):
        raise ValueError("'cantidad' debe ser un entero.")
    elif cantidad < 1:
        raise ValueError("'cantidad' debe ser mayor que cero.")

    minimo = min(numeros)
    maximo = max(numeros)
    if minimo == maximo:
        delta = abs(minimo) * 0.1 if minimo != 0 else 1.0
        minimo -= delta
        maximo += delta

    paso = (maximo - minimo) / cantidad
    conteos = [0] * cantidad
    for numero in numeros:
        indice = int((numero - minimo) / paso)
        if indice < 0:
            indice = 0
        elif indice >= cantidad:
            indice = cantidad - 1
        conteos[indice] += 1

    bordes = [minimo + indice * paso for indice in range(cantidad)]
    bordes.append(maximo)
    return bordes, conteos


# ---------------------------------------------------------------------- #
# Gráfica
# ---------------------------------------------------------------------- #

class Grafica:
    """Gráfica configurable que se rasteriza sobre un Lienzo."""

    def __init__(
        self,
        tipo,
        series,
        titulo="",
        etiqueta_x="",
        etiqueta_y="",
        leyenda="",
        ancho=800,
        alto=480,
    ):
        if tipo not in TIPOS:
            raise ValueError(
                "Tipo de gráfica desconocido {0!r}; los tipos válidos son: "
                "{1}.".format(tipo, ", ".join(TIPOS))
            )
        self.tipo = tipo
        self.series = list(series) if series is not None else []
        for serie in self.series:
            if not isinstance(serie, Serie):
                raise ValueError(
                    "Cada serie debe ser una instancia de Serie; recibí "
                    "{0!r}.".format(serie)
                )
        self.titulo = "" if titulo is None else str(titulo)
        self.etiqueta_x = "" if etiqueta_x is None else str(etiqueta_x)
        self.etiqueta_y = "" if etiqueta_y is None else str(etiqueta_y)
        self.leyenda = "" if leyenda is None else str(leyenda)
        self.ancho = ancho
        self.alto = alto

    # --------------------------- infraestructura --------------------- #

    def _area(self):
        """Devuelve (x0, y0, x1, y1) del área de trazado en píxeles."""
        x0 = MARGEN_IZQUIERDO
        y0 = MARGEN_SUPERIOR
        x1 = self.ancho - MARGEN_DERECHO
        y1 = self.alto - MARGEN_INFERIOR
        if x1 - x0 < 60 or y1 - y0 < 60:
            raise ValueError(
                "La gráfica es demasiado pequeña: se necesitan al menos "
                "162x188 píxeles para respetar los márgenes."
            )
        return x0, y0, x1, y1

    def _series_con_datos(self):
        """Series con al menos un valor y; error si no queda ninguna."""
        series = [serie for serie in self.series if serie.y]
        if not series:
            raise _sin_datos()
        return series

    def _entradas_leyenda(self, series):
        """Pares (nombre, color) para la leyenda."""
        return [
            (serie.nombre or "Serie {0}".format(indice + 1),
             PALETA[indice % len(PALETA)])
            for indice, serie in enumerate(series)
        ]

    def _titulo(self, lienzo):
        if not self.titulo:
            return
        escala = 2 if self.ancho >= 560 else 1
        texto = _recortar(
            self.titulo, self.ancho - 2 * MARGEN_IZQUIERDO, escala
        )
        ancho = lienzo.ancho_texto(texto, escala)
        lienzo.texto((self.ancho - ancho) // 2, 20, texto, _TITULO, escala)

    def _rejilla_y(self, lienzo, escala, cantidad=5):
        """Rejilla horizontal, etiquetas del eje y y líneas de los ejes."""
        x0, y0, x1, y1 = self._area()
        for valor in escala.ticks(cantidad):
            pixel = int(round(escala.mapear(valor)))
            if y0 <= pixel <= y1:
                lienzo.linea(x0 + 1, pixel, x1, pixel, _REJILLA)
            etiqueta = formatear(valor)
            texto = _recortar(etiqueta, MARGEN_IZQUIERDO - 16)
            ancho = lienzo.ancho_texto(texto)
            lienzo.texto(
                max(2, x0 - 8 - ancho), pixel - 3, texto, _TEXTO
            )
        lienzo.linea(x0, y0, x0, y1, _EJE)
        lienzo.linea(x0, y1, x1, y1, _EJE)

        if self.etiqueta_y:
            texto = _recortar(self.etiqueta_y, x1 - x0 - 10)
            lienzo.texto(x0 + 4, y0 - 20, texto, _EJE)

    def _eje_x(self, lienzo, posiciones, etiquetas, max_ancho=None):
        """Etiquetas del eje x completas y espaciadas, sin truncar en bloque.

        Si las etiquetas completas no caben, se dibuja una de cada k (ver
        _seleccionar_etiquetas()); solo se recorta una etiqueta cuando es
        más ancha que toda el área de trazado.
        """
        x0, y0, x1, y1 = self._area()
        total = min(len(posiciones), len(etiquetas))
        if total == 0:
            return
        posiciones = list(posiciones)[:total]
        ancho_area = max(1, x1 - x0)
        textos = [
            _acortar_etiqueta(etiqueta, ancho_area)
            for etiqueta in etiquetas[:total]
        ]
        if max_ancho is None:
            max_ancho = ancho_area
        indices = _seleccionar_etiquetas(posiciones, textos, max_ancho)

        for indice in indices:
            posicion = posiciones[indice]
            texto = textos[indice]
            ancho = lienzo.ancho_texto(texto)
            x = int(round(posicion)) - ancho // 2
            x = max(2, min(self.ancho - ancho - 2, x))
            lienzo.linea(int(round(posicion)), y1, int(round(posicion)), y1 + 4, _EJE)
            if texto:
                lienzo.texto(x, y1 + 8, texto, _TEXTO)

        if self.etiqueta_x:
            texto = _recortar(self.etiqueta_x, x1 - x0)
            ancho = lienzo.ancho_texto(texto)
            lienzo.texto(
                x0 + (x1 - x0 - ancho) // 2, self.alto - 22, texto, _EJE
            )

    def _leyenda(self, lienzo, entradas):
        """Recuadro de leyenda en la esquina superior derecha del área."""
        if not entradas and not self.leyenda:
            return
        x0, y0, x1, y1 = self._area()
        filas = len(entradas)
        anchos = [ancho_texto_fuente(texto) for texto, _ in entradas]
        if self.leyenda:
            anchos.append(ancho_texto_fuente(self.leyenda))
        ancho_texto = max(anchos) if anchos else 0
        ancho = ancho_texto + 34
        alto = 8 + (14 if self.leyenda else 0) + filas * 14 + 6

        derecha = x1 - 8
        izquierda = max(x0 + 8, derecha - ancho)
        arriba = y0 + 8
        lienzo.rectangulo_relleno(
            izquierda, arriba, derecha - izquierda, alto, _BLANCO
        )
        lienzo.rectangulo(
            izquierda, arriba, derecha - izquierda, alto, (215, 215, 215)
        )
        cursor = arriba + 5
        if self.leyenda:
            lienzo.texto(
                izquierda + 8, cursor, _recortar(self.leyenda, ancho - 16), _TEXTO
            )
            cursor += 14
        for indice, (texto, color) in enumerate(entradas):
            lienzo.rectangulo_relleno(
                izquierda + 8, cursor + 2, 10, 8, color
            )
            lienzo.texto(
                izquierda + 24,
                cursor + 1,
                _recortar(texto, ancho - 32),
                _TEXTO,
            )
            cursor += 14

    def _marcador(self, lienzo, x, y, forma, color, radio=3):
        """Dibuja un marcador pequeño con la forma pedida."""
        if forma == "cuadrado":
            lienzo.rectangulo_relleno(
                x - radio, y - radio, 2 * radio + 1, 2 * radio + 1, color
            )
        elif forma == "rombo":
            lienzo.linea(x, y - radio, x + radio, y, color)
            lienzo.linea(x + radio, y, x, y + radio, color)
            lienzo.linea(x, y + radio, x - radio, y, color)
            lienzo.linea(x - radio, y, x, y - radio, color)
        elif forma == "cruz":
            lienzo.linea(x - radio, y, x + radio, y, color)
            lienzo.linea(x, y - radio, x, y + radio, color)
        elif forma == "triangulo":
            lienzo.linea(x, y - radio, x + radio, y + radio, color)
            lienzo.linea(x + radio, y + radio, x - radio, y + radio, color)
            lienzo.linea(x - radio, y + radio, x, y - radio, color)
        else:
            lienzo.circulo_relleno(x, y, radio, color)

    # ------------------------------ puntos xy ------------------------ #

    def _extraer_puntos(self, series):
        """Normaliza (x, y) de cada serie y prepara la escala x.

        Si alguna x es textual, todas se tratan como categorías y se usa
        el índice de la categoría como coordenada. Devuelve
        (puntos_por_serie, escala_x, posiciones_x, etiquetas_x).
        """
        x0, y0, x1, y1 = self._area()
        textual = any(
            serie.x is not None and any(_numero(x) is None for x in serie.x)
            for serie in series
        )

        if textual:
            claves = {}
            categorias = []
            for serie in series:
                valores_x = (
                    serie.x if serie.x is not None else range(len(serie.y))
                )
                for valor_x in valores_x:
                    clave = _clave_categoria(valor_x)
                    if clave not in claves:
                        claves[clave] = len(categorias)
                        categorias.append(valor_x)
            puntos = []
            for serie in series:
                valores_x = (
                    serie.x if serie.x is not None else range(len(serie.y))
                )
                pares = []
                for valor_x, valor_y in zip(valores_x, serie.y):
                    numero_y = _numero(valor_y)
                    if numero_y is None:
                        continue
                    pares.append(
                        (claves[_clave_categoria(valor_x)], numero_y)
                    )
                puntos.append(pares)
            escala_x = EscalaLineal(-0.5, len(categorias) - 0.5, x0, x1)
            posiciones = [
                escala_x.mapear(indice) for indice in range(len(categorias))
            ]
            etiquetas = [_etiqueta_categoria(c) for c in categorias]
            return puntos, escala_x, posiciones, etiquetas

        puntos = []
        valores_x = []
        for serie in series:
            coordenadas_x = (
                serie.x if serie.x is not None else range(len(serie.y))
            )
            pares = []
            for valor_x, valor_y in zip(coordenadas_x, serie.y):
                numero_x = _numero(valor_x)
                numero_y = _numero(valor_y)
                if numero_x is None or numero_y is None:
                    continue
                pares.append((numero_x, numero_y))
                valores_x.append(numero_x)
            pares.sort(key=lambda par: par[0])
            puntos.append(pares)
        if not valores_x:
            raise _sin_datos()
        # En el eje x se respeta el dominio real de los datos con un
        # margen pequeño: extenderlo a múltiplos del paso bonito dejaba
        # series de 12 años ocupando solo la mitad del área.
        bajo = min(valores_x)
        alto = max(valores_x)
        if bajo == alto:
            bajo -= 1.0
            alto += 1.0
        margen = (alto - bajo) * 0.02
        escala_x = EscalaLineal(bajo - margen, alto + margen, x0, x1)
        marcas = escala_x.ticks(6)
        return (
            puntos,
            escala_x,
            [escala_x.mapear(marca) for marca in marcas],
            [formatear(marca) for marca in marcas],
        )

    # ------------------------------ barras -------------------------- #

    def _dibujar_barras(self, lienzo):
        series = self._series_con_datos()
        claves = {}
        categorias = []
        for serie in series:
            valores_x = (
                serie.x if serie.x is not None else range(len(serie.y))
            )
            for valor_x in valores_x:
                clave = _clave_categoria(valor_x)
                if clave not in claves:
                    claves[clave] = len(categorias)
                    categorias.append(valor_x)
        if not categorias:
            raise _sin_datos()

        acumulados = []
        todos = []
        for serie in series:
            valores_x = (
                serie.x if serie.x is not None else range(len(serie.y))
            )
            parcial = {}
            for valor_x, valor_y in zip(valores_x, serie.y):
                numero = _numero(valor_y)
                if numero is None:
                    continue
                indice = claves[_clave_categoria(valor_x)]
                # Categorías repetidas: se suman sus valores.
                parcial[indice] = parcial.get(indice, 0.0) + numero
            acumulados.append(parcial)
            todos.extend(parcial.values())
        if not todos:
            raise _sin_datos()

        x0, y0, x1, y1 = self._area()
        bajo, alto = _limites(todos, incluir_cero=True)
        escala_y = EscalaLineal(bajo, alto, y1, y0)
        self._rejilla_y(lienzo, escala_y)
        self._titulo(lienzo)

        banda = EscalaBanda(categorias, x0, x1, separacion=0.2)
        ancho_grupo = banda.ancho_banda * (1 - banda.separacion)
        ancho_barra = ancho_grupo / len(series)
        pixel_cero = escala_y.mapear(0.0)
        for indice_serie, parcial in enumerate(acumulados):
            color = PALETA[indice_serie % len(PALETA)]
            for indice_categoria, valor in parcial.items():
                centro = banda.mapear(categorias[indice_categoria])
                izquierda = centro - ancho_grupo / 2 + indice_serie * ancho_barra
                pixel_valor = escala_y.mapear(valor)
                arriba = int(round(min(pixel_valor, pixel_cero)))
                abajo = int(round(max(pixel_valor, pixel_cero)))
                lienzo.rectangulo_relleno(
                    int(round(izquierda)),
                    arriba,
                    max(1, int(round(ancho_barra))),
                    max(1, abajo - arriba),
                    color,
                )

        self._eje_x(
            lienzo,
            banda.posiciones(),
            [_etiqueta_categoria(c) for c in categorias],
            max(8, int(banda.ancho_banda) - 4),
        )
        if len(series) > 1 or self.leyenda:
            self._leyenda(lienzo, self._entradas_leyenda(series))
        return lienzo

    # ------------------------------ líneas -------------------------- #

    def _dibujar_lineas(self, lienzo):
        series = self._series_con_datos()
        puntos, escala_x, posiciones_x, etiquetas_x = self._extraer_puntos(
            series
        )
        valores_y = [
            numero for pares in puntos for _, numero in pares
        ]
        if not valores_y:
            raise _sin_datos()

        x0, y0, x1, y1 = self._area()
        bajo, alto = _limites(valores_y)
        escala_y = EscalaLineal(bajo, alto, y1, y0)
        self._rejilla_y(lienzo, escala_y)
        self._titulo(lienzo)

        for indice, pares in enumerate(puntos):
            color = PALETA[indice % len(PALETA)]
            pixeles = [
                (int(round(escala_x.mapear(x))), int(round(escala_y.mapear(y))))
                for x, y in pares
            ]
            for posicion in range(len(pixeles) - 1):
                lienzo.linea(
                    pixeles[posicion][0],
                    pixeles[posicion][1],
                    pixeles[posicion + 1][0],
                    pixeles[posicion + 1][1],
                    color,
                    grosor=2,
                )
            for x, y in pixeles:
                lienzo.circulo_relleno(x, y, 2, color)

        self._eje_x(lienzo, posiciones_x, etiquetas_x)
        if len(series) > 1 or self.leyenda:
            self._leyenda(lienzo, self._entradas_leyenda(series))
        return lienzo

    # ---------------------------- histograma ------------------------ #

    def _dibujar_histograma(self, lienzo):
        if not self.series:
            raise _sin_datos()
        # Solo se usa la primera serie, como define el tipo histograma.
        primera = self.series[0]
        valores = [
            numero for numero in (_numero(v) for v in primera.y)
            if numero is not None
        ]
        if not valores:
            raise _sin_datos()
        bordes, conteos = cubetas_histograma(valores)

        x0, y0, x1, y1 = self._area()
        escala_x = EscalaLineal(bordes[0], bordes[-1], x0, x1)
        bajo, alto = _limites(
            [0.0, float(max(conteos))], incluir_cero=True
        )
        escala_y = EscalaLineal(bajo, alto, y1, y0)
        self._rejilla_y(lienzo, escala_y)
        self._titulo(lienzo)

        ancho_banda = (x1 - x0) / len(conteos)
        base = escala_y.mapear(0.0)
        color = PALETA[0]
        for indice, conteo in enumerate(conteos):
            if conteo <= 0:
                continue
            izquierda = int(round(x0 + indice * ancho_banda))
            derecha = int(round(x0 + (indice + 1) * ancho_banda))
            arriba = int(round(escala_y.mapear(conteo)))
            lienzo.rectangulo_relleno(
                izquierda,
                arriba,
                max(1, derecha - izquierda),
                max(1, int(round(base)) - arriba),
                color,
            )

        etiquetas_rango = [
            "{0}-{1}".format(
                formatear(bordes[indice]), formatear(bordes[indice + 1])
            )
            for indice in range(len(conteos))
        ]
        ancho_rango = max(
            (ancho_texto_fuente(etiqueta) for etiqueta in etiquetas_rango),
            default=0,
        )
        if len(conteos) <= 12 and ancho_rango <= ancho_banda - 4:
            posiciones = [
                x0 + (indice + 0.5) * ancho_banda
                for indice in range(len(conteos))
            ]
            etiquetas = etiquetas_rango
            max_ancho = max(8, int(ancho_banda) - 4)
        else:
            posiciones = [escala_x.mapear(borde) for borde in bordes]
            etiquetas = [formatear(borde) for borde in bordes]
            max_ancho = None
        self._eje_x(lienzo, posiciones, etiquetas, max_ancho)

        if self.leyenda:
            self._leyenda(lienzo, self._entradas_leyenda([primera]))
        return lienzo

    # ---------------------------- dispersión ------------------------ #

    def _dibujar_dispersion(self, lienzo):
        series = self._series_con_datos()
        puntos, escala_x, posiciones_x, etiquetas_x = self._extraer_puntos(
            series
        )
        valores_y = [numero for pares in puntos for _, numero in pares]
        if not valores_y:
            raise _sin_datos()

        x0, y0, x1, y1 = self._area()
        bajo, alto = _limites(valores_y)
        escala_y = EscalaLineal(bajo, alto, y1, y0)
        self._rejilla_y(lienzo, escala_y)
        self._titulo(lienzo)

        formas = ("circulo", "cuadrado", "rombo", "cruz", "triangulo")
        for indice, pares in enumerate(puntos):
            color = PALETA[indice % len(PALETA)]
            forma = formas[indice % len(formas)]
            for x, y in pares:
                self._marcador(
                    lienzo,
                    int(round(escala_x.mapear(x))),
                    int(round(escala_y.mapear(y))),
                    forma,
                    color,
                    radio=3,
                )

        self._eje_x(lienzo, posiciones_x, etiquetas_x)
        if len(series) > 1 or self.leyenda:
            self._leyenda(lienzo, self._entradas_leyenda(series))
        return lienzo

    # ------------------------------- cajas -------------------------- #

    def _dibujar_cajas(self, lienzo):
        series = self._series_con_datos()
        x0, y0, x1, y1 = self._area()
        # Se agrupa por 'x' cuando sus valores se repiten: así una columna
        # de décadas, ciudades o años produce una caja por grupo, aunque
        # el eje sea numérico. Si cada x es única (por ejemplo el índice
        # de fila que pone el runtime), hay una caja por serie.
        valores_x = [
            valor
            for serie in series
            for valor in (serie.x if serie.x is not None else ())
        ]
        claves_x = {_clave_categoria(valor) for valor in valores_x}
        agrupada = bool(valores_x) and len(claves_x) < len(valores_x)

        grupos = []  # (etiqueta, valores, color)
        if agrupada:
            claves = {}
            categorias = []
            for serie in series:
                valores_x = (
                    serie.x if serie.x is not None else range(len(serie.y))
                )
                for valor_x in valores_x:
                    clave = _clave_categoria(valor_x)
                    if clave not in claves:
                        claves[clave] = len(categorias)
                        categorias.append(valor_x)
            acumulado = {indice: [] for indice in range(len(categorias))}
            for serie in series:
                valores_x = (
                    serie.x if serie.x is not None else range(len(serie.y))
                )
                for valor_x, valor_y in zip(valores_x, serie.y):
                    numero = _numero(valor_y)
                    if numero is None:
                        continue
                    acumulado[claves[_clave_categoria(valor_x)]].append(numero)
            for indice, categoria in enumerate(categorias):
                if acumulado[indice]:
                    grupos.append(
                        (
                            _etiqueta_categoria(categoria),
                            acumulado[indice],
                            PALETA[indice % len(PALETA)],
                        )
                    )
        else:
            for indice, serie in enumerate(series):
                valores = [
                    numero for numero in (_numero(v) for v in serie.y)
                    if numero is not None
                ]
                if valores:
                    grupos.append(
                        (
                            serie.nombre or "Serie {0}".format(indice + 1),
                            valores,
                            PALETA[indice % len(PALETA)],
                        )
                    )
        if not grupos:
            raise _sin_datos()

        todos = [valor for _, valores, _ in grupos for valor in valores]
        bajo, alto = _limites(todos)
        escala_y = EscalaLineal(bajo, alto, y1, y0)
        self._rejilla_y(lienzo, escala_y)
        self._titulo(lienzo)

        banda = EscalaBanda(
            list(range(len(grupos))), x0, x1, separacion=0.4
        )
        ancho_caja = min(90.0, banda.ancho_banda * (1 - banda.separacion))
        for indice, (etiqueta, valores, color) in enumerate(grupos):
            cuartil_1, mediana, cuartil_3 = cuartiles(valores)
            rango_inter = cuartil_3 - cuartil_1
            limite_inferior = cuartil_1 - 1.5 * rango_inter
            limite_superior = cuartil_3 + 1.5 * rango_inter
            dentro = [
                valor for valor in valores
                if limite_inferior <= valor <= limite_superior
            ]
            bigote_inferior = min(dentro) if dentro else cuartil_1
            bigote_superior = max(dentro) if dentro else cuartil_3
            atipicos = [
                valor for valor in valores
                if valor < limite_inferior or valor > limite_superior
            ]

            centro = int(round(banda.mapear(indice)))
            izquierda = int(round(centro - ancho_caja / 2))
            ancho = max(4, int(round(ancho_caja)))
            arriba = int(round(escala_y.mapear(cuartil_3)))
            abajo = int(round(escala_y.mapear(cuartil_1)))
            alto_caja = max(1, abajo - arriba)

            lienzo.rectangulo_relleno(
                izquierda, arriba, ancho, alto_caja, _aclarar(color, 0.75)
            )
            lienzo.rectangulo(
                izquierda, arriba, ancho, alto_caja, color, grosor=2
            )
            lienzo.linea(
                izquierda,
                int(round(escala_y.mapear(mediana))),
                izquierda + ancho - 1,
                int(round(escala_y.mapear(mediana))),
                color,
                grosor=2,
            )

            pixel_superior = int(round(escala_y.mapear(bigote_superior)))
            pixel_inferior = int(round(escala_y.mapear(bigote_inferior)))
            lienzo.linea(centro, arriba, centro, pixel_superior, color)
            lienzo.linea(centro, pixel_inferior, centro, abajo, color)
            mitad = max(3, ancho // 4)
            lienzo.linea(
                centro - mitad, pixel_superior, centro + mitad,
                pixel_superior, color,
            )
            lienzo.linea(
                centro - mitad, pixel_inferior, centro + mitad,
                pixel_inferior, color,
            )
            for valor in atipicos:
                lienzo.circulo_relleno(
                    centro, int(round(escala_y.mapear(valor))), 2, color
                )

        self._eje_x(
            lienzo,
            banda.posiciones(),
            [etiqueta for etiqueta, _, _ in grupos],
            max(8, int(banda.ancho_banda) - 4),
        )
        if self.leyenda:
            self._leyenda(
                lienzo,
                [
                    (etiqueta, color)
                    for etiqueta, _, color in grupos
                ],
            )
        return lienzo

    # ------------------------------ público ------------------------- #

    def renderizar(self):
        """Rasteriza la gráfica y devuelve el Lienzo resultante."""
        lienzo = Lienzo(self.ancho, self.alto)
        self._area()  # valida el tamaño antes de dibujar
        metodo = getattr(self, "_dibujar_" + self.tipo)
        return metodo(lienzo)


# ---------------------------------------------------------------------- #
# Conveniencia
# ---------------------------------------------------------------------- #

def dibujar(tipo, series, **opciones):
    """Crea y rasteriza una gráfica en una sola llamada.

    'opciones' se pasa tal cual a Grafica: titulo, etiqueta_x,
    etiqueta_y, leyenda, ancho y alto.
    """
    return Grafica(tipo, series, **opciones).renderizar()
