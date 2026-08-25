"""
AREPA - Columna propia (src/datos/columna.py)
---------------------------------------------
Implementado por el equipo. Una Columna guarda el nombre y el tipo
inferido de un campo de la Tabla. Los valores viven en las filas; la
columna es el metadato.

Qué hace:
  * conservar el nombre original del encabezado;
  * conservar el tipo declarado o inferido ('numero', 'texto', 'logico',
    'fecha') usando el sistema propio de tipos.

Limitaciones:
  * una columna mezclada (números y texto) se tipa como 'texto'.
"""

from datos.tipos import inferir_tipo


class Columna:
    """Metadato de un campo: nombre y tipo."""

    __slots__ = ("nombre", "tipo")

    def __init__(self, nombre, tipo="texto"):
        self.nombre = nombre
        self.tipo = tipo

    def __repr__(self):
        return "Columna({0}, {1})".format(self.nombre, self.tipo)

    @staticmethod
    def inferir(nombre, valores):
        """Crea una columna infiriendo el tipo con el sistema propio."""
        return Columna(nombre, inferir_tipo(valores))
