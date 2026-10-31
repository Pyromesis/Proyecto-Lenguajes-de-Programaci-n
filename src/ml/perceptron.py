"""
AREPA - Perceptrón propio (src/ml/perceptron.py)
------------------------------------------------
Implementado por el equipo desde cero. Es el clasificador lineal binario
clásico: aprende un vector de pesos y un sesgo con la regla del perceptrón

    si y * (w·x + b) <= 0:
        w = w + tasa * y * x
        b = b + tasa * y

donde y es +1 para la primera clase y -1 para la segunda. Las variables
llegan estandarizadas por el Preprocesador. No usa numpy, sklearn ni
ninguna biblioteca de machine learning.
"""

from datos.tipos import formatear_numero
from errores_base import ErrorSemantico

from ml.modelo import (
    ModeloClasificacion,
    exigir_entero_positivo,
    exigir_numero_positivo,
)


class Perceptron(ModeloClasificacion):
    """Clasificador lineal binario entrenado con la regla del perceptrón."""

    def __init__(self, preprocesador, objetivo, tasa=0.1, epocas=200, clases=None):
        super().__init__(preprocesador, objetivo)
        self.tasa = exigir_numero_positivo(tasa, "tasa")
        self.epocas = exigir_entero_positivo(epocas, "epocas")
        self.clases = list(clases) if clases else None
        self.pesos = []
        self.sesgo = 0.0
        self.entrenado = False

    def entrenar(self, X, y):
        if not X:
            raise ErrorSemantico("El perceptrón no recibió filas para entrenar.")
        self.clases = self._resolver_clases(y)
        if len(self.clases) != 2:
            raise ErrorSemantico(
                "El perceptrón es binario: necesita exactamente 2 clases, pero "
                "encontré {0} ({1}). Para más clases usá 'arbol'.".format(
                    len(self.clases), ", ".join(_texto(c) for c in self.clases)
                )
            )
        etiquetas = {clase: (1.0 if i == 0 else -1.0) for i, clase in enumerate(self.clases)}
        for valor in y:
            if valor not in etiquetas:
                raise ErrorSemantico(
                    "La etiqueta '{0}' no está en 'clases [{1}]'.".format(
                        _texto(valor), ", ".join(_texto(c) for c in self.clases)
                    )
                )

        dimension = len(X[0])
        if any(len(fila) != dimension for fila in X):
            raise ErrorSemantico("Las filas de entrenamiento tienen dimensiones distintas.")
        self.pesos = [0.0 for _ in range(dimension)]
        self.sesgo = 0.0

        for epoca in range(1, self.epocas + 1):
            errores = 0
            for fila, valor in zip(X, y):
                esperado = etiquetas[valor]
                puntaje = self._producto_punto(self.pesos, fila) + self.sesgo
                if esperado * puntaje <= 0:
                    for j in range(dimension):
                        self.pesos[j] += self.tasa * esperado * fila[j]
                    self.sesgo += self.tasa * esperado
                    errores += 1
            self.historial.append(errores)
            self.epocas_reales = epoca
            if errores == 0:
                break

        self.entrenado = True
        return self

    def predecir(self, vector):
        if not self.entrenado:
            raise ErrorSemantico("El perceptrón todavía no está entrenado.")
        if len(vector) != len(self.pesos):
            raise ErrorSemantico(
                "La fila tiene {0} variables y el modelo espera {1}.".format(
                    len(vector), len(self.pesos)
                )
            )
        puntaje = self._producto_punto(self.pesos, vector) + self.sesgo
        return self.clases[0] if puntaje >= 0 else self.clases[1]

    def resumen(self):
        lineas = self._encabezado_resumen()
        lineas.append(
            "  entrenamiento: regla del perceptrón, tasa={0}, épocas={1}".format(
                formatear_numero(self.tasa), self.epocas
            )
        )
        lineas.append(
            "  clases: {0} (+1) y {1} (-1)".format(
                _texto(self.clases[0]) if self.clases else "?",
                _texto(self.clases[1]) if self.clases and len(self.clases) > 1 else "?",
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
                "  errores en la última época: {0}".format(self.historial[-1])
            )
        return "\n".join(lineas)

    def _resolver_clases(self, y):
        if self.clases:
            return list(self.clases)
        clases = []
        vistas = set()
        for valor in y:
            if valor not in vistas:
                vistas.add(valor)
                clases.append(valor)
        return clases

    @staticmethod
    def _producto_punto(a, b):
        return sum(x * y for x, y in zip(a, b))


def _texto(valor):
    if isinstance(valor, bool):
        return "obvio" if valor else "falso"
    return str(valor)
