"""
AREPA - Lista propia (src/datos/lista.py)
-----------------------------------------
Implementado por el equipo. Arreglo dinámico propio del DSL, sin usar
bibliotecas externas: el tipo list de Python se usa solo como almacenamiento
interno, igual que Tabla usa list para sus filas.

Qué hace:
  * guardar elementos en orden de inserción;
  * dar acceso por índice interno 0-based con validación de rango;
  * agregar, reemplazar y quitar elementos;
  * copiar la lista de forma superficial.

Decisiones propias documentadas:
  * los índices son 0-based; la semántica 1-based del lenguaje la aplica
    el runtime al traducir el índice;
  * 'quitar' devuelve el elemento eliminado;
  * los errores de rango son ErrorEjecucion e incluyen el largo actual.

Limitaciones:
  * no se admiten índices negativos: -1 no significa "el último";
  * la copia es superficial (los elementos anidados se comparten).
"""

from errores_base import ErrorEjecucion


class Lista:
    """Arreglo dinámico propio: elementos en orden e índices desde 0."""

    __slots__ = ("_elementos",)

    def __init__(self, elementos=None):
        """Crea la lista copiando 'elementos' (iterable opcional)."""
        self._elementos = list(elementos) if elementos is not None else []

    # ---------------------------------------------------------------- #
    # Consulta y acceso
    # ---------------------------------------------------------------- #

    def largo(self):
        """Cantidad de elementos guardados."""
        return len(self._elementos)

    def obtener(self, indice):
        """Devuelve el elemento en la posición interna 'indice'.

        Lanza ErrorEjecucion si el índice no es entero o está fuera de
        rango; el mensaje indica el largo de la lista.
        """
        self._validar_indice(indice, "obtener")
        return self._elementos[indice]

    # ---------------------------------------------------------------- #
    # Modificación
    # ---------------------------------------------------------------- #

    def poner(self, indice, valor):
        """Reemplaza el elemento en 'indice' (debe existir)."""
        self._validar_indice(indice, "poner")
        self._elementos[indice] = valor

    def agregar(self, valor):
        """Agrega 'valor' al final de la lista."""
        self._elementos.append(valor)

    def quitar(self, indice):
        """Elimina y devuelve el elemento en 'indice'."""
        self._validar_indice(indice, "quitar")
        return self._elementos.pop(indice)

    def copiar(self):
        """Nueva Lista con los mismos elementos (copia superficial)."""
        return Lista(self._elementos)

    # ---------------------------------------------------------------- #
    # Validación interna
    # ---------------------------------------------------------------- #

    def _validar_indice(self, indice, operacion):
        """Comprueba que 'indice' sea un entero dentro del rango válido."""
        if not isinstance(indice, int) or isinstance(indice, bool):
            raise ErrorEjecucion(
                "El índice de la lista debe ser un numero entero; "
                "recibí {0} en '{1}'.".format(repr(indice), operacion)
            )
        if indice < 0 or indice >= len(self._elementos):
            raise ErrorEjecucion(
                "No existe el índice {0} en la lista ('{1}'): el largo es {2}.".format(
                    indice, operacion, len(self._elementos)
                )
            )

    # ---------------------------------------------------------------- #
    # Protocolos de Python
    # ---------------------------------------------------------------- #

    def __len__(self):
        return len(self._elementos)

    def __iter__(self):
        """Itera los elementos (no los índices)."""
        return iter(self._elementos)

    def __eq__(self, otro):
        return isinstance(otro, Lista) and self._elementos == otro._elementos

    def __repr__(self):
        return "Lista({0!r})".format(self._elementos)
