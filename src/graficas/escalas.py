"""
AREPA - Escalas de las gráficas (src/graficas/escalas.py)
---------------------------------------------------------
Implementadas por el equipo. Traducen valores del dominio de los datos a
coordenadas de píxel y eligen las marcas ("ticks") que se muestran en
los ejes. No se usan bibliotecas externas.

Qué hace:
  * EscalaLineal: mapeo afín dominio -> rango, su inverso y ticks con
    pasos "bonitos" de la forma 1, 2 o 5 por una potencia de diez;
  * EscalaBanda: reparte categorías en bandas iguales y mapea cada una
    al centro de su banda (lo que necesitan barras y cajas);
  * formatear: número a etiqueta legible (enteros sin decimales, el
    resto con 1 o 2, sin notación científica salvo valores extremos).

Decisiones propias documentadas:
  * un dominio degenerado (minimo == maximo) se expande para que el
    mapeo no divida por cero: +-1 si el valor es cero y +-10 % en otro
    caso;
  * los ticks se generan dentro del dominio, alineados a múltiplos del
    paso; si no caben al menos dos, se devuelven los extremos;
  * los valores no finitos (NaN, infinito) se rechazan con ValueError:
    las gráficas filtran antes esos valores, la escala no los inventa;
  * EscalaBanda rechaza categorías repetidas porque el agrupamiento (por
    ejemplo, la suma en barras) debe resolverse antes de construirla.

Limitaciones:
  * no hay escalas logarítmicas ni de fechas;
  * EscalaBanda distingue número de texto: 1 y "1" son categorías
    distintas (el motor de gráficas sí las unifica al agrupar).
"""

import math

# ---------------------------------------------------------------------- #
# Validaciones y utilidades numéricas
# ---------------------------------------------------------------------- #

def _a_float(valor, nombre="valor"):
    """Convierte a float finito o lanza ValueError explicativo."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(
            "'{0}' debe ser un número; recibí {1!r}.".format(nombre, valor)
        )
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError(
            "'{0}' debe ser un número finito; recibí {1!r}.".format(nombre, valor)
        )
    return numero


def _clave_categoria(categoria):
    """Clave comparable y hashable para una categoría."""
    if isinstance(categoria, bool):
        return ("n", float(categoria))
    if isinstance(categoria, (int, float)):
        numero = float(categoria)
        if math.isfinite(numero):
            return ("n", numero)
        return ("s", str(categoria))
    if categoria is None:
        return ("s", "nada")
    if isinstance(categoria, str):
        return ("s", categoria)
    try:
        hash(categoria)
    except TypeError:
        raise ValueError(
            "la categoría {0!r} no es hashable.".format(categoria)
        )
    return ("s", str(categoria))


def _decimales(paso):
    """Decimales necesarios para escribir múltiplos de 'paso' sin ruido."""
    if paso <= 0 or not math.isfinite(paso):
        return 0
    exponente = math.floor(math.log10(paso))
    return max(0, -exponente) + 2


def _redondear(valor, paso):
    """Redondea 'valor' para eliminar el error de la coma flotante."""
    return round(valor, _decimales(paso))


# ---------------------------------------------------------------------- #
# Paso "bonito" y formato
# ---------------------------------------------------------------------- #

def paso_bonito(rango, cantidad=5):
    """Paso de eje de la forma 1, 2 o 5 por 10^k que cubre 'rango'.

    Se usa tanto para generar ticks como para extender el dominio de una
    gráfica hasta múltiplos exactos del paso.
    """
    rango = abs(_a_float(rango, "rango"))
    if isinstance(cantidad, bool) or not isinstance(cantidad, int):
        raise ValueError("'cantidad' debe ser un entero.")
    cantidad = max(1, cantidad)
    if rango == 0:
        return 1.0

    bruto = rango / cantidad
    magnitud = 10.0 ** math.floor(math.log10(bruto))
    fraccion = bruto / magnitud
    if fraccion <= 1:
        factor = 1
    elif fraccion <= 2:
        factor = 2
    elif fraccion <= 5:
        factor = 5
    else:
        factor = 10
    return _redondear(factor * magnitud, factor * magnitud)


def formatear(valor):
    """Etiqueta legible para un valor de eje.

    Enteros sin decimales, el resto con uno o dos decimales. Solo los
    valores extremos (>= 1e7 o < 1e-4) usan notación científica.
    """
    if valor is None:
        return "nada"
    if isinstance(valor, str):
        return valor
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if not math.isfinite(numero):
        return "nada"
    if numero == 0:
        return "0"

    absoluto = abs(numero)
    if absoluto >= 1e7 or absoluto < 1e-4:
        mantisa, exponente = "{0:.2e}".format(numero).split("e")
        mantisa = mantisa.rstrip("0").rstrip(".")
        return "{0}e{1:+d}".format(mantisa, int(exponente))
    if abs(numero - round(numero)) < 1e-9:
        return str(int(round(numero)))
    if absoluto < 10:
        return "{0:.2f}".format(numero).rstrip("0").rstrip(".")
    return "{0:.1f}".format(numero).rstrip("0").rstrip(".")


# ---------------------------------------------------------------------- #
# Escala lineal
# ---------------------------------------------------------------------- #

class EscalaLineal:
    """Mapeo afín entre un dominio numérico y un rango en píxeles."""

    __slots__ = ("dominio_min", "dominio_max", "rango_min", "rango_max")

    def __init__(self, dominio_min, dominio_max, rango_min, rango_max):
        minimo = _a_float(dominio_min, "dominio_min")
        maximo = _a_float(dominio_max, "dominio_max")
        self.rango_min = _a_float(rango_min, "rango_min")
        self.rango_max = _a_float(rango_max, "rango_max")
        if self.rango_min == self.rango_max:
            raise ValueError(
                "el rango de píxeles no puede ser degenerado: "
                "rango_min y rango_max deben ser distintos."
            )

        if minimo == maximo:
            delta = abs(minimo) * 0.1 if minimo != 0 else 1.0
            minimo -= delta
            maximo += delta
        elif minimo > maximo:
            minimo, maximo = maximo, minimo

        self.dominio_min = minimo
        self.dominio_max = maximo

    def mapear(self, valor):
        """Convierte un valor del dominio a su coordenada en el rango."""
        numero = _a_float(valor, "valor")
        fraccion = (numero - self.dominio_min) / (
            self.dominio_max - self.dominio_min
        )
        return self.rango_min + fraccion * (self.rango_max - self.rango_min)

    def invertir(self, pixel):
        """Convierte una coordenada del rango al valor del dominio."""
        numero = _a_float(pixel, "pixel")
        fraccion = (numero - self.rango_min) / (
            self.rango_max - self.rango_min
        )
        return self.dominio_min + fraccion * (
            self.dominio_max - self.dominio_min
        )

    def ticks(self, cantidad=5):
        """Valores "bonitos" dentro del dominio, alineados al paso."""
        if isinstance(cantidad, bool) or not isinstance(cantidad, int):
            raise ValueError("'cantidad' debe ser un entero.")
        if cantidad < 1:
            raise ValueError("'cantidad' debe ser mayor que cero.")

        paso = paso_bonito(self.dominio_max - self.dominio_min, cantidad)
        inicio = math.ceil(self.dominio_min / paso - 1e-9) * paso
        marcas = []
        valor = inicio
        # El tope con holgura relativa evita perder la última marca por
        # el error de la suma repetida de un paso decimal.
        while valor <= self.dominio_max + paso * 1e-9:
            marcas.append(_redondear(valor, paso))
            valor += paso
        if len(marcas) < 2:
            marcas = [
                _redondear(self.dominio_min, paso),
                _redondear(self.dominio_max, paso),
            ]
        return marcas


# ---------------------------------------------------------------------- #
# Escala de bandas (categorías)
# ---------------------------------------------------------------------- #

class EscalaBanda:
    """Reparte categorías en bandas iguales dentro de un rango."""

    __slots__ = (
        "categorias",
        "rango_min",
        "rango_max",
        "separacion",
        "ancho_banda",
        "_indices",
    )

    def __init__(self, categorias, rango_min, rango_max, separacion=0.2):
        categorias = list(categorias)
        if not categorias:
            raise ValueError("La escala de banda necesita al menos una categoría.")
        claves = [_clave_categoria(categoria) for categoria in categorias]
        if len(set(claves)) != len(claves):
            raise ValueError(
                "La escala de banda no admite categorías repetidas."
            )
        self.categorias = categorias
        self._indices = {clave: i for i, clave in enumerate(claves)}

        self.rango_min = _a_float(rango_min, "rango_min")
        self.rango_max = _a_float(rango_max, "rango_max")
        if self.rango_min == self.rango_max:
            raise ValueError("El rango de la escala de banda no puede ser degenerado.")

        separacion = _a_float(separacion, "separacion")
        if not 0 <= separacion < 1:
            raise ValueError(
                "'separacion' debe estar entre 0 y 1 (sin incluir 1); "
                "recibí {0}.".format(separacion)
            )
        self.separacion = separacion
        self.ancho_banda = (self.rango_max - self.rango_min) / len(categorias)

    def mapear(self, categoria):
        """Coordenada del centro de la banda de 'categoria'."""
        indice = self._indices.get(_clave_categoria(categoria))
        if indice is None:
            raise ValueError(
                "La categoría {0!r} no pertenece a la escala.".format(categoria)
            )
        return self.rango_min + (indice + 0.5) * self.ancho_banda

    def posiciones(self):
        """Centros de todas las bandas, en el orden de las categorías."""
        return [
            self.rango_min + (indice + 0.5) * self.ancho_banda
            for indice in range(len(self.categorias))
        ]
