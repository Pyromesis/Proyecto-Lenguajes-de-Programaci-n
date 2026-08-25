"""
AREPA - Fila propia (src/datos/fila.py)
---------------------------------------
Implementado por el equipo. Una Fila es un registro de la Tabla: una
lista de valores ordenada según las columnas de su tabla.

Qué hace:
  * guardar los valores de un registro;
  * dar acceso posicional y por nombre (con el mapa de la tabla).

Limitaciones:
  * la fila no conoce su tabla: el acceso por nombre lo resuelve Tabla,
    que sí conserva el mapa nombre -> posición.
"""


class Fila:
    """Registro de datos: valores en el orden de las columnas."""

    __slots__ = ("valores",)

    def __init__(self, valores=None):
        self.valores = list(valores) if valores else []

    def __len__(self):
        return len(self.valores)

    def __eq__(self, otro):
        return isinstance(otro, Fila) and self.valores == otro.valores

    def __repr__(self):
        return "Fila({0})".format(self.valores)

    def copiar(self):
        return Fila(self.valores)

    def valor_en(self, indice):
        return self.valores[indice]

    def poner_en(self, indice, valor):
        self.valores[indice] = valor

    def agregar(self, valor):
        self.valores.append(valor)
