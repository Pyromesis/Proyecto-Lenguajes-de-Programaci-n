"""
AREPA - Tabla de símbolos propia (src/runtime/simbolos.py)
----------------------------------------------------------
Implementado por el equipo. Almacena variables y funciones del programa
con ámbitos encadenados (un ámbito hijo consulta a su padre).

Qué hace:
  * declarar variables en el ámbito actual;
  * asignar a una variable existente en cualquier ámbito visible;
  * buscar valores subiendo por la cadena de ámbitos;
  * detectar variables inexistentes con ErrorVariable comprensible;
  * validar identificadores con la regla propia del DSL (letra/ñ/tilde
    o '_', seguido de letras, dígitos o '_');
  * guardar funciones definidas con 'invente' junto a su ámbito de
    definición (closures), lo que permite recursión.

Decisiones:
  * 'x = valor' declara en el ámbito actual si no existe en la cadena
    (semántica tipo Python, documentada);
  * los bloques de fijese_si NO crean ámbito propio; solo las funciones.
"""

import re

from errores_base import ErrorSemantico, ErrorVariable

PATRON_IDENTIFICADOR = re.compile(r"^[^\W\d]\w*$", re.UNICODE)


def validar_identificador(nombre):
    """Lanza ErrorSemantico si el nombre no es un identificador válido."""
    if not PATRON_IDENTIFICADOR.match(nombre):
        raise ErrorSemantico(
            "'{0}' no es un nombre válido para una variable: debe iniciar con "
            "una letra y contener solo letras, dígitos o guion bajo.".format(nombre)
        )
    return nombre


class Simbolo:
    """Una entrada de la tabla: nombre y su valor actual."""

    __slots__ = ("nombre", "valor")

    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

    def __repr__(self):
        return "Simbolo({0})".format(self.nombre)


class TablaSimbolos:
    """Diccionario de nombres con cadena de ámbitos (padre)."""

    def __init__(self, padre=None):
        self.padre = padre
        self._entradas = {}

    # ---------------------------------------------------------------- #

    def declarar(self, nombre, valor):
        """Declara o sobrescribe en el ámbito ACTUAL."""
        validar_identificador(nombre)
        self._entradas[nombre] = Simbolo(nombre, valor)
        return valor

    def asignar(self, nombre, valor):
        """Asigna a una variable existente en este ámbito o en un padre."""
        if nombre in self._entradas:
            self._entradas[nombre].valor = valor
            return valor
        if self.padre is not None:
            return self.padre.asignar(nombre, valor)
        raise ErrorVariable(
            "No puedo asignar a '{0}' porque no existe; declarala primero "
            "con '{0} = ...'.".format(nombre)
        )

    def buscar(self, nombre):
        """Valor de una variable; ErrorVariable si no existe en ningún ámbito."""
        simbolo = self._entradas.get(nombre)
        if simbolo is not None:
            return simbolo.valor
        if self.padre is not None:
            return self.padre.buscar(nombre)
        raise ErrorVariable(
            "La variable '{0}' no está declarada. Declarala antes con "
            "'{0} = ...'.".format(nombre)
        )

    def buscar_opcional(self, nombre):
        """Valor o None si el nombre no existe en la cadena de ámbitos."""
        try:
            return self.buscar(nombre)
        except ErrorVariable:
            return None

    def existe(self, nombre):
        """True si el nombre está declarado en este ámbito o en un padre."""
        if nombre in self._entradas:
            return True
        return self.padre is not None and self.padre.existe(nombre)

    def existe_local(self, nombre):
        return nombre in self._entradas

    def hijo(self):
        """Crea un ámbito hijo (para llamadas a funciones)."""
        return TablaSimbolos(padre=self)


class FuncionArepa:
    """Función definida con 'invente': parámetros, cuerpo y closure."""

    __slots__ = ("nombre", "parametros", "nodo_bloque", "entorno")

    def __init__(self, nombre, parametros, nodo_bloque, entorno):
        self.nombre = nombre
        self.parametros = parametros
        self.nodo_bloque = nodo_bloque
        self.entorno = entorno

    def __repr__(self):
        return "FuncionArepa({0}({1}))".format(
            self.nombre, ", ".join(self.parametros)
        )
