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
  * registrar los archivos producidos por 'guarde' (CSV) y por 'pinte'
    (PNG) con su ruta, tipo y cantidad de bytes;
  * permitir capturar la salida desde las pruebas.

Limitaciones:
  * la salida se imprime en consola y se acumula en memoria; no hay
    redirección a archivo (no se pide en el corte).
"""

import sys

from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import es_infinito, es_nada, es_logico, formatear_numero
from runtime.simbolos import TablaSimbolos


def a_texto(valor):
    """Convierte un valor del DSL a texto legible con reglas propias."""
    if es_nada(valor):
        return "nada"
    if es_logico(valor):
        return "obvio" if valor else "falso"
    if isinstance(valor, Tabla):
        return "\n" + valor.texto_tabla()
    if isinstance(valor, Lista):
        return _texto_lista(valor)
    if isinstance(valor, Registro):
        return _texto_registro(valor)
    if es_infinito(valor):
        return formatear_numero(valor)
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    if isinstance(valor, str):
        return valor
    return str(valor)


def _texto_contenido(valor):
    """Texto de un valor dentro de una lista o registro.

    A diferencia de a_texto(), los textos van entre comillas dobles (como
    en el ejemplo {nombre: "Ana", edad: 20}); el resto de los tipos usa el
    formato normal y las estructuras se anidan de forma recursiva.
    """
    if isinstance(valor, str):
        return '"{0}"'.format(valor.replace('"', '\\"'))
    if isinstance(valor, Lista):
        return _texto_lista(valor)
    if isinstance(valor, Registro):
        return _texto_registro(valor)
    if isinstance(valor, Tabla):
        return valor.texto_tabla()
    return a_texto(valor)


def _texto_lista(lista):
    """Formato propio de una Lista: [1, 2, 3]."""
    return "[{0}]".format(", ".join(_texto_contenido(v) for v in lista))


def _texto_registro(registro):
    """Formato propio de un Registro: {nombre: "Ana", edad: 20}."""
    partes = [
        "{0}: {1}".format(clave, _texto_contenido(valor))
        for clave, valor in zip(registro.claves(), registro.valores())
    ]
    return "{{{0}}}".format(", ".join(partes))


class ContextoEjecucion:
    """Estado global del programa: símbolos raíz, salida y errores vistos.

    'errores' registra los problemas que ocurrieron durante la corrida
    (el ejecutor lanza la excepción para interrumpir y la CLI la
    reporta; además queda archivada aquí para inspección y pruebas).
    """

    def __init__(self):
        self.simbolos = TablaSimbolos()
        self.salida = []
        self.errores = []
        self.archivos_generados = []

    def imprimir(self, *valores):
        """Registra (y muestra) los valores separados por espacio."""
        linea = " ".join(a_texto(v) for v in valores)
        self.salida.append(linea)
        print(linea)
        sys.stdout.flush()

    def registrar_error(self, problema):
        """Archiva un error propio ocurrido durante la ejecución."""
        self.errores.append(problema)

    def registrar_archivo(self, ruta, tipo, bytes_escritos):
        """Archiva un archivo producido por el programa (csv o png).

        Devuelve el diccionario recién guardado para que quien llama pueda
        consultar el tamaño sin volver a buscarlo en la lista.
        """
        registro = {
            "ruta": ruta,
            "tipo": tipo,
            "bytes": bytes_escritos,
        }
        self.archivos_generados.append(registro)
        return registro
