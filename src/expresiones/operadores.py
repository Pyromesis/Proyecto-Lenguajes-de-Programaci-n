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
   * dividir entre cero NO es error: 1/0 produce 'infinito', -1/0
     produce '-infinito' y 0/0 produce 'nada' (indefinido);
   * el módulo entre cero NO es error: produce 'nada' (indefinido);
   * el indefinido punto flotante ('nan', p. ej. infinito + (-infinito))
     se vuelve 'nada' en aritmética y desviación;
   * la potencia que desborda produce 'infinito' (con su signo); solo
     sigue siendo error el resultado complejo (p. ej. (-1) ^ 0.5).

Limitaciones:
  * no hay coerción numero<->texto en '+' (la concatenación no existe en
    el DSL a propósito: el catálogo no la define).
"""

from datos.tipos import (
    INFINITO,
    MENOS_INFINITO,
    NADA,
    es_nada,
    es_numero,
    es_texto,
    es_logico,
    nombre_tipo,
)
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


def _sin_nan(valor):
    """Regla propia: el indefinido punto flotante ('nan') se vuelve 'nada'.

    Así combinaciones como infinito + (-infinito) no tumban el programa
    ni muestran 'nan': producen el faltante del DSL.
    """
    if isinstance(valor, float) and valor != valor:
        return NADA
    return valor


def sumar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "+")
    return _sin_nan(a + b)


def restar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "-")
    return _sin_nan(a - b)


def multiplicar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "*")
    return _sin_nan(a * b)


def dividir(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "/")
    if b == 0:
        if a == 0:
            return NADA
        return INFINITO if a > 0 else MENOS_INFINITO
    return _sin_nan(a / b)


def modulo(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "%")
    if b == 0:
        return NADA
    return _sin_nan(a % b)


def potenciar(a, b):
    if _propagar_nada(a, b):
        return NADA
    _exigir_numeros(a, b, "^")
    try:
        resultado = a ** b
    except ZeroDivisionError:
        return INFINITO
    except OverflowError:
        return _infinito_con_signo(a, b)
    if isinstance(resultado, complex):
        raise ErrorOperacion(
            "La potencia {0} ^ {1} no tiene resultado real.".format(a, b)
        )
    if resultado == INFINITO:
        return INFINITO
    if resultado == MENOS_INFINITO:
        return MENOS_INFINITO
    return _sin_nan(resultado)


def _infinito_con_signo(base, expo):
    """Infinito con el signo que tendría el resultado desbordado."""
    try:
        if base < 0 and float(expo).is_integer() and int(expo) % 2 == 1:
            return MENOS_INFINITO
    except (TypeError, ValueError):
        pass
    return INFINITO


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
