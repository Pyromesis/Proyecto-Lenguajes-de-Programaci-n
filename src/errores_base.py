"""
AREPA - Sistema propio de errores de la biblioteca del lenguaje
---------------------------------------------------------------
Jerarquía de excepciones implementada por el equipo para todo el
runtime del DSL (datos, expresiones y ejecución).

Cada error carga:
  * mensaje: descripción comprensible en español;
  * linea / columna: ubicación en el programa .arepa cuando se conoce;
  * contexto: fragmento del programa o de datos que ayudó a detectarlo.

La ubicación conserva el nodo más específico disponible: operador, acceso
o instrucción. En CSV se distingue la línea de datos de la del programa.
"""


class ErrorArepa(Exception):
    """Base de todos los errores propios del DSL."""

    def __init__(self, mensaje, linea=-1, columna=-1, contexto=""):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        self.contexto = contexto
        self.archivo_datos = ""
        self.llamadas = []

    def __str__(self):
        ubicacion = ""
        if self.linea >= 1:
            ubicacion = "Línea {0}".format(self.linea)
            if self.columna >= 0:
                ubicacion += ", Columna {0}".format(self.columna)
            ubicacion += ": "
        return ubicacion + self.mensaje


# ---------------------------------------------------------------------- #
# Errores semánticos: el programa es sintácticamente válido pero usa
# mal el lenguaje (variables, columnas, tipos, operaciones).
# ---------------------------------------------------------------------- #

class ErrorSemantico(ErrorArepa):
    """Error de significado: nombres, tipos o uso incorrecto del DSL."""


class ErrorVariable(ErrorSemantico):
    """Se usa una variable que no ha sido declarada con una asignación."""


class ErrorColumna(ErrorSemantico):
    """Se referencia una columna que no existe en la tabla actual."""


class ErrorTipos(ErrorSemantico):
    """Operación entre valores de tipos incompatibles."""


class ErrorOperacion(ErrorSemantico):
    """Operación inválida aunque los tipos sean razonables."""


# ---------------------------------------------------------------------- #
# Errores de ejecución: el programa falla al correr (archivos, datos).
# ---------------------------------------------------------------------- #

class ErrorEjecucion(ErrorArepa):
    """Fallo durante la ejecución del programa."""


class ErrorArchivo(ErrorEjecucion):
    """Un archivo referenciado no existe o no se pudo leer."""


class ErrorCSV(ErrorArchivo):
    """El archivo CSV tiene un formato que el lector propio no acepta."""

    def __init__(self, mensaje, linea_archivo=-1, linea=-1, columna=-1, contexto=""):
        super().__init__(mensaje, linea, columna, contexto)
        self.linea_archivo = linea_archivo


class ErrorGrafica(ErrorEjecucion):
    """La instrucción 'pinte' no puede construir o guardar la gráfica."""


# ---------------------------------------------------------------------- #
# Control de flujo interno (no es un error): usada por 'devuelva' para
# salir de la ejecución de una función con su valor.
# ---------------------------------------------------------------------- #

class RetornoFuncion(Exception):
    """Señal interna de 'devuelva': transporta el valor de retorno."""

    def __init__(self, valor):
        super().__init__("retorno de función")
        self.valor = valor


# ---------------------------------------------------------------------- #
# Control de flujo de ciclos (no es un error): 'pare' rompe el ciclo más
# cercano y 'siga' salta a la siguiente vuelta. Si escapan de todo ciclo,
# el ejecutor las convierte en ErrorSemantico con línea y columna.
# ---------------------------------------------------------------------- #

class SalirCiclo(Exception):
    """Señal interna de 'pare': rompe el ciclo 'repita'/'mientras' activo."""

    def __init__(self, linea=-1, columna=-1):
        super().__init__("salir de ciclo")
        self.linea = linea
        self.columna = columna


class SeguirCiclo(Exception):
    """Señal interna de 'siga': salta a la siguiente vuelta del ciclo."""

    def __init__(self, linea=-1, columna=-1):
        super().__init__("seguir en ciclo")
        self.linea = linea
        self.columna = columna


def completar_ubicacion(problema, nodo):
    """Conserva la ubicación más interna; completa solo la desconocida."""
    # CommonToken.start es un índice de caracteres, no otro token.
    token = nodo if hasattr(nodo, "line") else getattr(nodo, "start", None)
    if problema.linea < 1 and token is not None:
        problema.linea = getattr(token, "line", -1)
        problema.columna = getattr(token, "column", -1)
    return problema
