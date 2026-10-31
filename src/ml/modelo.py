"""
AREPA - Modelos supervisados propios (src/ml/modelo.py)
-------------------------------------------------------
Implementado por el equipo. Define la interfaz común de los modelos de
machine learning del DSL y el puente con la Tabla propia.

Un modelo guarda:
  * el preprocesador aprendido (imputación, one-hot y estandarización);
  * la columna objetivo;
  * sus hiperparámetros y su estado entrenado.

La predicción de una fila se hace con 'predecir_fila', que transforma la
fila con exactamente la misma codificación usada en el entrenamiento.
"""

from datos.tipos import NADA, es_nada, es_numero, formatear_numero
from errores_base import ErrorSemantico


class ModeloML:
    """Interfaz común de todos los modelos de AREPA."""

    tipo_arepa = "modelo"
    tarea = "modelo"
    estandarizar = False

    def __init__(self, preprocesador, objetivo):
        self.preprocesador = preprocesador
        self.objetivo = objetivo
        self.nombre = "modelo"
        self.epocas = 0
        self.historial = []

    # ---------------------------------------------------------------- #
    # Entrenamiento y predicción
    # ---------------------------------------------------------------- #

    def entrenar(self, X, y):
        raise NotImplementedError

    def predecir(self, vector):
        raise NotImplementedError

    def predecir_fila(self, fila, tabla):
        """Predice una fila de una tabla usando la codificación aprendida."""
        vector = self.preprocesador.transformar_fila(
            fila, tabla, estandarizar=self.estandarizar
        )
        return self._valor_seguro(self.predecir(vector))

    def evaluar(self, tabla):
        """Devuelve (reales, predicciones) sobre una tabla con el objetivo."""
        X, y = self.preprocesador.datos(tabla, estandarizar=self.estandarizar)
        if isinstance(self, ModeloRegresion):
            self.validar_objetivo(y)
        predicciones = [self.predecir(vector) for vector in X]
        return y, predicciones

    # ---------------------------------------------------------------- #
    # Presentación
    # ---------------------------------------------------------------- #

    def resumen(self):
        return "{0} '{1}' (tarea: {2})".format(
            self.__class__.__name__, self.nombre, self.tarea
        )

    def _encabezado_resumen(self):
        return [
            "{0} '{1}' (tarea: {2})".format(
                self.__class__.__name__, self.nombre, self.tarea
            ),
            "  objetivo: {0}".format(self.objetivo),
            "  columnas: {0}".format(", ".join(self.preprocesador.columnas)),
            "  preprocesamiento: {0}".format(self.preprocesador.resumen()),
        ]

    def _valor_seguro(self, valor):
        """Convierte NaN/infinito en 'nada' para no romper una tabla."""
        if isinstance(valor, float) and (valor != valor or valor in (float("inf"), float("-inf"))):
            return NADA
        return valor


class ModeloRegresion(ModeloML):
    """Modelo que predice un número continuo."""

    tipo_arepa = "regresion"
    tarea = "regresion"
    estandarizar = True

    def validar_objetivo(self, y):
        """Exige que todas las etiquetas del objetivo sean numéricas."""
        for valor in y:
            if not es_numero(valor):
                raise ErrorSemantico(
                    "La regresión necesita un objetivo numérico, pero "
                    "encontré '{0}'. Para etiquetas usá 'perceptron' o "
                    "'arbol'.".format(valor)
                )


class ModeloClasificacion(ModeloML):
    """Modelo que predice una etiqueta discreta."""

    tipo_arepa = "clasificacion"
    tarea = "clasificacion"
    estandarizar = True


# ---------------------------------------------------------------------- #
# Validación de hiperparámetros compartida
# ---------------------------------------------------------------------- #

def exigir_entero_positivo(valor, nombre, contexto=""):
    if es_nada(valor) or not isinstance(valor, int) or isinstance(valor, bool):
        raise ErrorSemantico(
            "'{0}' debe ser un número entero positivo{1}.".format(
                nombre, _donde(contexto)
            )
        )
    if valor <= 0:
        raise ErrorSemantico(
            "'{0}' debe ser mayor que 0{1}.".format(nombre, _donde(contexto))
        )
    return valor


def exigir_numero_positivo(valor, nombre, contexto=""):
    if es_nada(valor) or not es_numero(valor) or valor <= 0:
        raise ErrorSemantico(
            "'{0}' debe ser un número mayor que 0{1}.".format(
                nombre, _donde(contexto)
            )
        )
    return float(valor)


def _donde(contexto):
    return " ({0})".format(contexto) if contexto else ""


def texto_numero(valor):
    return formatear_numero(valor)


def es_etiqueta_valida(valor):
    return not es_nada(valor)
