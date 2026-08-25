"""
AREPA - Operadores propios (src/expresiones/operadores.py)
----------------------------------------------------------
Implementado por el equipo. Cada operador del DSL es una función propia
que valida tipos con el sistema propio (datos.tipos) y decide qué hacer
con el valor faltante 'nada'.

Reglas semánticas decididas por el equipo:
  * 'nada' se propaga: cualquier operación aritmética o comparación con
    'nada' produce 'nada' (estilo SQL);
  * los operadores lógicos exigen valores lógicos (obvio/falso) o 'nada',
    que también se propaga;
  * una comparación entre numero y texto lanza ErrorTipos (no hay
    coerción silenciosa);
  * dividir o sacar módulo entre cero lanza ErrorOperacion.

Limitaciones:
  * no hay coerción numero<->texto en '+' (la concatenación no existe en
    el DSL a propósito: el catálogo no la define).
"""

from datos.tipos import NADA, es_nada, es_numero, es_texto, es_logico, nombre_tipo
from errores_base import ErrorOperacion, ErrorTipos


def _exigir_numeros(a, b, operador):
    for v, lado in ((a, "izquierdo"), (b, "derecho")):
        if not es_numero(v):
            raise ErrorTipos(
                "El operador '{0}' necesita números, pero el valor {1} es de "
                "tipo {2}.".format(operador, lado, nombre_tipo(v))
            )


def _propagar_nada(a, b):
    """Regla propia: si algún operando es 'nada', el resultado es 'nada'."""
    return es_nada(a) or es_nada(b)


def sumar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "+")
    return a + b


def restar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "-")
    return a - b


def multiplicar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "*")
    return a * b


def dividir(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "/")
    if b == 0:
        raise ErrorOperacion("No se puede dividir entre cero.")
    return a / b


def modulo(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "%")
    if b == 0:
        raise ErrorOperacion("No se puede calcular el módulo entre cero.")
    return a % b


def potenciar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "^")
    try:
        return a ** b
    except (OverflowError, ZeroDivisionError):
        raise ErrorOperacion(
            "La potencia {0} ^ {1} no se puede calcular.".format(a, b)
        )


def negar_numero(v):
    if es_nada(v):
        return NADA
    if not es_numero(v):
        raise ErrorTipos(
            "El signo '-' necesita un número, pero recibí un valor de tipo "
            "{0}.".format(nombre_tipo(v))
        )
    return -v


# --------------------------------------------------------------------- #
# Relacionales: comparan solo valores del mismo género (número con
# número, texto con texto, lógico con lógico); 'nada' se propaga.
# --------------------------------------------------------------------- #

def _comparables(a, b, operador):
    if es_nada(a) or es_nada(b):
        return False
    generos = (es_numero(a), es_texto(a), es_logico(a))
    if generos != (es_numero(b), es_texto(b), es_logico(b)):
        raise ErrorTipos(
            "No puedo comparar un valor de tipo {0} con uno de tipo {1} "
            "usando '{2}'.".format(nombre_tipo(a), nombre_tipo(b), operador)
        )
    return True


def igual(a, b):
    if es_nada(a) or es_nada(b):
        return NADA
    _comparables(a, b, "==")
    return a == b


def diferente(a, b):
    if es_nada(a) or es_nada(b):
        return NADA
    _comparables(a, b, "!=")
    return a != b


def menor(a, b):
    if _comparables(a, b, "<"):
        return a < b
    return NADA


def menor_igual(a, b):
    if _comparables(a, b, "<="):
        return a <= b
    return NADA


def mayor(a, b):
    if _comparables(a, b, ">"):
        return a > b
    return NADA


def mayor_igual(a, b):
    if _comparables(a, b, ">="):
        return a >= b
    return NADA


# --------------------------------------------------------------------- #
# Lógicos: exigen booleanos; 'nada' se propaga.
# --------------------------------------------------------------------- #

def _exigir_logico(v, operador, lado=""):
    if not es_logico(v):
        raise ErrorTipos(
            "El operador '{0}' necesita valores lógicos (obvio/falso), pero "
            "{1} recibí un valor de tipo {2}.".format(
                operador, "en el lado " + lado if lado else "", nombre_tipo(v)
            )
        )


def conjuncion(a, b):
    if es_nada(a) or es_nada(b):
        return NADA
    _exigir_logico(a, "y", "izquierdo")
    _exigir_logico(b, "y", "derecho")
    return a and b


def disyuncion(a, b):
    if es_nada(a) or es_nada(b):
        return NADA
    _exigir_logico(a, "o", "izquierdo")
    _exigir_logico(b, "o", "derecho")
    return a or b


def negar_logico(v):
    if es_nada(v):
        return NADA
    _exigir_logico(v, "no")
    return not v
