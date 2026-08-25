"""
AREPA - Pruebas del evaluador de expresiones propio (src/expresiones)
---------------------------------------------------------------------
Evalúa expresiones reales del DSL parseándolas con la gramática ANTLR4
(autorizada) y ejecutándolas con el runtime propio. Cubre aritmética,
precedencia, relacionales, lógicos, 'nada' y errores de tipos.

Uso:
    python pruebas/test_expresiones.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.tipos import NADA  # noqa: E402
from errores_base import ErrorTipos, ErrorOperacion  # noqa: E402
from lenguaje.analizador import analizar  # noqa: E402
from runtime.ejecutor import EjecutorArepa  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


def valor_de(expresion):
    """Parsea 'x = <expresion>' y ejecuta con el runtime propio."""
    programa = "quihubo\nx = {0}\nchao\n".format(expresion)
    _, arbol, errores = analizar(programa)
    assert not errores, "la expresión '{0}' no parseó: {1}".format(expresion, errores)
    ejecutor = EjecutorArepa()
    ejecutor.ejecutar(arbol)
    return ejecutor.contexto.simbolos.buscar("x")


# ---------------------------------------------------------------------- #
# Aritmética y precedencia
# ---------------------------------------------------------------------- #

@caso
def aritmetica_basica():
    assert valor_de("2 + 3") == 5
    assert valor_de("10 - 4") == 6
    assert valor_de("6 * 7") == 42
    assert valor_de("7 / 2") == 3.5
    assert valor_de("7 % 3") == 1


@caso
def precedencia_multiplicacion_sobre_suma():
    assert valor_de("1 + 2 * 3") == 7
    assert valor_de("(1 + 2) * 3") == 9


@caso
def potencia_asociativa_a_derecha():
    assert valor_de("2 ^ 3 ^ 2") == 512  # 2^(3^2), no (2^3)^2


@caso
def unarios_y_negativos():
    assert valor_de("-5") == -5
    assert valor_de("-5 + 10") == 5
    assert valor_de("2 ^ -3") == 0.125
    assert valor_de("--5") == 5


@caso
def parentesis_anidados():
    assert valor_de("((1 + 2) * (3 + 4)) / 7") == 3


# ---------------------------------------------------------------------- #
# Relacionales y lógicos
# ---------------------------------------------------------------------- #

@caso
def comparaciones_numericas():
    assert valor_de("3 < 5") is True
    assert valor_de("5 <= 5") is True
    assert valor_de("6 > 9") is False
    assert valor_de("6 >= 9") is False
    assert valor_de("4 == 4") is True
    assert valor_de("4 != 4") is False


@caso
def comparaciones_de_textos():
    assert valor_de('"ana" == "ana"') is True
    assert valor_de('"ana" != "bruno"') is True
    assert valor_de('"ana" < "bruno"') is True


@caso
def logicos_y_o_no():
    assert valor_de("obvio y falso") is False
    assert valor_de("obvio o falso") is True
    assert valor_de("no falso") is True
    assert valor_de("no no obvio") is True
    assert valor_de("(2 > 1) y (3 != 4)") is True


# ---------------------------------------------------------------------- #
# Valor faltante 'nada'
# ---------------------------------------------------------------------- #

@caso
def nada_se_propaga():
    assert valor_de("nada + 1") is NADA
    assert valor_de("1 * nada") is NADA
    assert valor_de("nada == nada") is NADA
    assert valor_de("nada < 5") is NADA
    assert valor_de("obvio y nada") is NADA
    assert valor_de("no nada") is NADA


# ---------------------------------------------------------------------- #
# Errores de tipos y operaciones
# ---------------------------------------------------------------------- #

@caso
def suma_numero_mas_texto_rechazada():
    try:
        valor_de('1 + "a"')
        raise AssertionError("numero + texto debería fallar")
    except ErrorTipos as e:
        assert "números" in e.mensaje


@caso
def comparacion_numero_con_texto_rechazada():
    try:
        valor_de('1 < "a"')
        raise AssertionError("numero < texto debería fallar")
    except ErrorTipos as e:
        assert "comparar" in e.mensaje


@caso
def logico_con_numero_rechazado():
    try:
        valor_de("obvio y 1")
        raise AssertionError("'y' con número debería fallar")
    except ErrorTipos as e:
        assert "lógicos" in e.mensaje


@caso
def division_entre_cero_rechazada():
    try:
        valor_de("5 / 0")
        raise AssertionError("división entre cero debería fallar")
    except ErrorOperacion as e:
        assert "cero" in e.mensaje


@caso
def modulo_entre_cero_rechazado():
    try:
        valor_de("5 % 0")
        raise AssertionError("módulo entre cero debería fallar")
    except ErrorOperacion:
        pass


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DEL EVALUADOR DE EXPRESIONES PROPIO")
    print("=" * 78)
    for funcion in CASOS:
        try:
            funcion()
            pasaron += 1
            print("[PASÓ ] {0}".format(funcion.__name__))
        except AssertionError as problema:
            fallaron += 1
            print("[FALLÓ] {0}: {1}".format(funcion.__name__, problema))
        except Exception as problema:
            fallaron += 1
            print("[FALLÓ] {0}: excepción {1}".format(funcion.__name__, problema))
    print("-" * 78)
    print("Resultado: {0} de {1} pasaron".format(pasaron, len(CASOS)))
    return 0 if fallaron == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
