"""
AREPA - Contexto de ejecución propio (src/runtime/contexto.py)
--------------------------------------------------------------
Implementado por el equipo. Reúne el estado global del programa en
marcha: la tabla de símbolos raíz y la salida producida por 'cuenteme'
y por las instrucciones informativas.

Qué hace:
  * conservar el estado del programa (símbolos globales);
  * acumular la salida del programa con formato propio (sin tabulate ni
    pprint): números, textos, lógicos, 'nada' y tablas propias;
  * permitir capturar la salida desde las pruebas.

Limitaciones:
  * la salida se imprime en consola y se acumula en memoria; no hay
    redirección a archivo (no se pide en el corte).
"""

import sys

from datos.tabla import Tabla
from datos.tipos import es_nada, es_logico
from runtime.simbolos import TablaSimbolos


def a_texto(valor):
    """Convierte un valor del DSL a texto legible con reglas propias."""
    if es_nada(valor):
        return "nada"
    if es_logico(valor):
        return "obvio" if valor else "falso"
    if isinstance(valor, Tabla):
        return "\n" + valor.texto_tabla()
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    if isinstance(valor, str):
        return valor
    return str(valor)


class ContextoEjecucion:
    """Estado global del programa: símbolos raíz y salida acumulada."""

    def __init__(self):
        self.simbolos = TablaSimbolos()
        self.salida = []

    def imprimir(self, *valores):
        """Registra (y muestra) los valores separados por espacio."""
        linea = " ".join(a_texto(v) for v in valores)
        self.salida.append(linea)
        print(linea)
        sys.stdout.flush()
