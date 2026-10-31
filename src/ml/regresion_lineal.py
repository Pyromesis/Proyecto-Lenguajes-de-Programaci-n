"""
AREPA - Regresión lineal propia (src/ml/regresion_lineal.py)
------------------------------------------------------------
Implementado por el equipo desde cero. Ajusta un modelo lineal

    y = b + w1*x1 + w2*x2 + ... + wn*xn

con descenso de gradiente por lotes (batch gradient descent), tal como
se describe en los libros de referencia del proyecto. No usa numpy,
pandas, sklearn ni ninguna otra biblioteca de machine learning.

Las variables de entrada llegan estandarizadas por el Preprocesador
(media 0, desviación 1), lo que estabiliza el descenso de gradiente.
La salida se devuelve en la escala original del objetivo.
"""

from datos.tipos import formatear_numero
from errores_base import ErrorSemantico

from ml.modelo import ModeloRegresion, exigir_entero_positivo, exigir_numero_positivo


class RegresionLineal(ModeloRegresion):
    """Regresión lineal múltiple entrenada con descenso de gradiente."""

    def __init__(self, preprocesador, objetivo, tasa=0.05, epocas=1000):
        super().__init__(preprocesador, objetivo)
        self.tasa = exigir_numero_positivo(tasa, "tasa")
        self.epocas = exigir_entero_positivo(epocas, "epocas")
        self.pesos = []
        self.sesgo = 0.0
        self.entrenado = False

    def entrenar(self, X, y):
        if not X:
            raise ErrorSemantico("La regresión lineal no recibió filas para entrenar.")
        dimension = len(X[0])
        if dimension == 0:
            raise ErrorSemantico("La regresión lineal necesita al menos una columna.")
        if any(len(fila) != dimension for fila in X):
            raise ErrorSemantico("Las filas de entrenamiento tienen dimensiones distintas.")
        if len(y) != len(X):
            raise ErrorSemantico(
                "La regresión recibió {0} fila(s) y {1} etiqueta(s); deben "
                "coincidir.".format(len(X), len(y))
            )
        self.validar_objetivo(y)

        self.pesos = [0.0 for _ in range(dimension)]
        self.sesgo = sum(y) / len(y)
        n = len(X)
        error_previo = None

        for epoca in range(1, self.epocas + 1):
            predicciones = [
                self._producto_punto(self.pesos, fila) + self.sesgo for fila in X
            ]
            errores = [
                predicciones[i] - y[i] for i in range(n)
            ]

            gradientes = [0.0 for _ in range(dimension)]
            for i in range(n):
                error = errores[i]
                fila = X[i]
                for j in range(dimension):
                    gradientes[j] += error * fila[j]
            for j in range(dimension):
                gradientes[j] = (2.0 / n) * gradientes[j]
            gradiente_sesgo = (2.0 / n) * sum(errores)

            for j in range(dimension):
                self.pesos[j] -= self.tasa * gradientes[j]
            self.sesgo -= self.tasa * gradiente_sesgo

            mse = sum(error * error for error in errores) / n
            self.historial.append(mse)
            self.epocas_reales = epoca

            if error_previo is not None and abs(error_previo - mse) < 1e-14:
                break
            error_previo = mse

        self.entrenado = True
        return self

    def predecir(self, vector):
        if not self.entrenado:
            raise ErrorSemantico("La regresión lineal todavía no está entrenada.")
        if len(vector) != len(self.pesos):
            raise ErrorSemantico(
                "La fila tiene {0} variables y el modelo espera {1}.".format(
                    len(vector), len(self.pesos)
                )
            )
        return self._producto_punto(self.pesos, vector) + self.sesgo

    def resumen(self):
        lineas = self._encabezado_resumen()
        lineas.append(
            "  entrenamiento: descenso de gradiente, tasa={0}, épocas={1}".format(
                formatear_numero(self.tasa), self.epocas
            )
        )
        if self.pesos:
            pesos = ", ".join(
                "{0}={1}".format(nombre, formatear_numero(round(peso, 4)))
                for nombre, peso in zip(self.preprocesador.nombres_features, self.pesos)
            )
            lineas.append("  pesos: {0}".format(pesos))
            lineas.append("  sesgo: {0}".format(formatear_numero(round(self.sesgo, 4))))
        if self.historial:
            lineas.append(
                "  MSE final de entrenamiento: {0}".format(
                    formatear_numero(round(self.historial[-1], 4))
                )
            )
        return "\n".join(lineas)

    @staticmethod
    def _producto_punto(a, b):
        return sum(x * y for x, y in zip(a, b))
