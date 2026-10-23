"""
AREPA - Registro propio (src/datos/registro.py)
-----------------------------------------------
Implementado por el equipo. Estructura clave -> valor que conserva el orden
de inserción, sin usar dict ni collections.OrderedDict: el almacenamiento
son dos listas paralelas y la búsqueda de claves es lineal.

Qué hace:
  * guardar pares (clave, valor) en orden de primera aparición;
  * consultar, actualizar y agregar claves;
  * notificar cada 'poner' mediante un callback opcional 'al_poner'
    (lo usa Tabla para reflejar los cambios en su fila).

Decisiones propias documentadas:
  * si una clave se repite, actualiza su valor sin moverla de posición;
  * 'al_poner' se invoca en cada poner(), incluida la actualización;
  * los pares iniciales del constructor NO disparan 'al_poner' (son la
    carga inicial, no un cambio posterior);
  * 'copiar' no conserva el callback: la copia es independiente.

Limitaciones:
  * búsqueda lineal por clave (adecuada para registros pequeños);
  * las claves deben ser comparables por igualdad (texto en el DSL).
"""

from errores_base import ErrorColumna


class Registro:
    """Pares clave -> valor en orden de inserción, con búsqueda lineal."""

    __slots__ = ("_claves", "_valores", "_al_poner")

    def __init__(self, pares=None, al_poner=None):
        """Crea el registro desde 'pares' (iterable de tuplas clave, valor).

        'al_poner' es un callable opcional (clave, valor) que se invoca
        cada vez que se llama a poner().
        """
        self._claves = []
        self._valores = []
        self._al_poner = al_poner
        if pares is not None:
            for clave, valor in pares:
                indice = self._indice(clave)
                if indice is None:
                    self._claves.append(clave)
                    self._valores.append(valor)
                else:
                    self._valores[indice] = valor

    # ---------------------------------------------------------------- #
    # Consulta
    # ---------------------------------------------------------------- #

    def obtener(self, clave):
        """Valor asociado a 'clave'; ErrorColumna si no existe."""
        indice = self._indice(clave)
        if indice is None:
            raise ErrorColumna(
                "La clave '{0}' no existe en el registro. Claves disponibles: {1}.".format(
                    clave, self._lista_claves()
                )
            )
        return self._valores[indice]

    def tiene(self, clave):
        """True si la clave está en el registro."""
        return self._indice(clave) is not None

    def claves(self):
        """Lista de claves en orden de inserción."""
        return list(self._claves)

    def valores(self):
        """Lista de valores en el orden de sus claves."""
        return list(self._valores)

    def largo(self):
        """Cantidad de pares guardados."""
        return len(self._claves)

    # ---------------------------------------------------------------- #
    # Modificación
    # ---------------------------------------------------------------- #

    def poner(self, clave, valor):
        """Actualiza 'clave' o la agrega al final si no existía.

        Después del cambio invoca 'al_poner' si fue provisto.
        """
        indice = self._indice(clave)
        if indice is None:
            self._claves.append(clave)
            self._valores.append(valor)
        else:
            self._valores[indice] = valor
        if self._al_poner is not None:
            self._al_poner(clave, valor)

    def copiar(self):
        """Nueva copia independiente, sin callback 'al_poner'."""
        return Registro(zip(self._claves, self._valores))

    # ---------------------------------------------------------------- #
    # Utilidades internas
    # ---------------------------------------------------------------- #

    def _indice(self, clave):
        """Posición de 'clave' o None si no existe (búsqueda lineal)."""
        for i, actual in enumerate(self._claves):
            if actual == clave:
                return i
        return None

    def _lista_claves(self):
        """Texto con las claves disponibles para los mensajes de error."""
        if not self._claves:
            return "(ninguna)"
        return ", ".join(str(c) for c in self._claves)

    # ---------------------------------------------------------------- #
    # Protocolos de Python
    # ---------------------------------------------------------------- #

    def __len__(self):
        return len(self._claves)

    def __iter__(self):
        """Itera las claves en orden de inserción."""
        return iter(self._claves)

    def __eq__(self, otro):
        return (
            isinstance(otro, Registro)
            and self._claves == otro._claves
            and self._valores == otro._valores
        )

    def __repr__(self):
        return "Registro({0!r})".format(list(zip(self._claves, self._valores)))
