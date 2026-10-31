"""
AREPA - Árbol de decisión propio (src/ml/arbol_decision.py)
-----------------------------------------------------------
Implementado por el equipo desde cero. Construye un árbol de decisión
de clasificación con la idea de CART:

  * en cada nodo prueba todas las preguntas del tipo "columna <= umbral";
  * mide la impureza de Gini de cada división;
  * escoge la pregunta que más reduce la impureza (mayor ganancia);
  * repite recursivamente hasta que el nodo es puro o se alcanza
    'profundidad' / 'min_hojas'.

Las columnas categóricas llegan convertidas a one-hot por el
Preprocesador, así que el árbol también puede preguntar por categorías
("¿la categoría está presente?"). No usa sklearn, numpy ni pandas.
"""

from datos.tipos import formatear_numero
from errores_base import ErrorSemantico

from ml.modelo import ModeloClasificacion, exigir_entero_positivo


class NodoArbol:
    """Nodo interno (pregunta) u hoja (clase) del árbol."""

    __slots__ = ("indice", "umbral", "izquierda", "derecha", "clase", "conteo", "total")

    def __init__(self):
        self.indice = None
        self.umbral = None
        self.izquierda = None
        self.derecha = None
        self.clase = None
        self.conteo = {}
        self.total = 0

    @property
    def es_hoja(self):
        return self.clase is not None


class ArbolDecision(ModeloClasificacion):
    """Árbol de decisión de clasificación con impureza de Gini."""

    estandarizar = False

    def __init__(self, preprocesador, objetivo, profundidad=6, min_hojas=2, clases=None):
        super().__init__(preprocesador, objetivo)
        self.profundidad = exigir_entero_positivo(profundidad, "profundidad")
        self.min_hojas = exigir_entero_positivo(min_hojas, "min_hojas")
        self.clases = list(clases) if clases else None
        self.raiz = None
        self.entrenado = False
        self.exactitud_entrenamiento = 0.0

    def entrenar(self, X, y):
        if not X:
            raise ErrorSemantico("El árbol no recibió filas para entrenar.")
        dimension = len(X[0])
        if dimension == 0:
            raise ErrorSemantico("El árbol necesita al menos una columna de entrada.")
        if any(len(fila) != dimension for fila in X):
            raise ErrorSemantico("Las filas de entrenamiento tienen dimensiones distintas.")
        self.clases = self._resolver_clases(y)
        for valor in y:
            if valor not in self.clases:
                raise ErrorSemantico(
                    "La etiqueta '{0}' no está en 'clases'.".format(_texto(valor))
                )
        self.raiz = self._construir(X, y, list(range(len(y))), 0)
        self.entrenado = True
        aciertos = sum(
            1 for fila, valor in zip(X, y) if self.predecir(fila) == valor
        )
        self.exactitud_entrenamiento = aciertos / len(y)
        return self

    def predecir(self, vector):
        if not self.entrenado:
            raise ErrorSemantico("El árbol todavía no está entrenado.")
        nodo = self.raiz
        while not nodo.es_hoja:
            if len(vector) <= nodo.indice:
                raise ErrorSemantico(
                    "La fila tiene menos variables de las que espera el árbol."
                )
            if vector[nodo.indice] <= nodo.umbral:
                nodo = nodo.izquierda
            else:
                nodo = nodo.derecha
        return nodo.clase

    def resumen(self):
        lineas = self._encabezado_resumen()
        lineas.append(
            "  entrenamiento: CART/Gini, profundidad={0}, min_hojas={1}".format(
                self.profundidad, self.min_hojas
            )
        )
        lineas.append(
            "  clases: {0}".format(", ".join(_texto(c) for c in self.clases or []))
        )
        lineas.append(
            "  exactitud de entrenamiento: {0}".format(
                formatear_numero(self.exactitud_entrenamiento)
            )
        )
        lineas.append("  árbol:")
        lineas.extend(self._texto_nodo(self.raiz, 2))
        return "\n".join(lineas)

    # ---------------------------------------------------------------- #
    # Construcción recursiva
    # ---------------------------------------------------------------- #

    def _construir(self, X, y, indices, profundidad):
        conteo = self._conteo(y, indices)
        nodo = NodoArbol()
        nodo.conteo = conteo
        nodo.total = len(indices)
        nodo.clase = self._mayoria(conteo)

        if (
            len(conteo) <= 1
            or profundidad >= self.profundidad
            or len(indices) < self.min_hojas
        ):
            return nodo

        mejor = self._mejor_division(X, y, indices)
        if mejor is None or mejor[2] <= 1e-12:
            return nodo

        indice, umbral, _ganancia = mejor
        izquierda = []
        derecha = []
        for i in indices:
            if X[i][indice] <= umbral:
                izquierda.append(i)
            else:
                derecha.append(i)
        if not izquierda or not derecha:
            return nodo

        nodo.clase = None
        nodo.indice = indice
        nodo.umbral = umbral
        nodo.izquierda = self._construir(X, y, izquierda, profundidad + 1)
        nodo.derecha = self._construir(X, y, derecha, profundidad + 1)
        return nodo

    def _mejor_division(self, X, y, indices):
        impureza_padre = self._gini(y, indices)
        mejor = None
        cantidad = len(indices)
        for indice in range(len(X[0])):
            valores = sorted({X[i][indice] for i in indices})
            if len(valores) < 2:
                continue
            for umbral in self._umbrales(valores):
                izquierda = []
                derecha = []
                for i in indices:
                    if X[i][indice] <= umbral:
                        izquierda.append(i)
                    else:
                        derecha.append(i)
                if not izquierda or not derecha:
                    continue
                impureza = (
                    len(izquierda) / cantidad * self._gini(y, izquierda)
                    + len(derecha) / cantidad * self._gini(y, derecha)
                )
                ganancia = impureza_padre - impureza
                if mejor is None or ganancia > mejor[2]:
                    mejor = (indice, umbral, ganancia)
        return mejor

    @staticmethod
    def _umbrales(valores):
        """Puntos medios entre valores; como máximo 64 cortes por columna."""
        if len(valores) <= 65:
            seleccion = valores
        else:
            paso = max(1, len(valores) // 64)
            seleccion = valores[::paso]
            if seleccion[-1] != valores[-1]:
                seleccion.append(valores[-1])
        umbrales = []
        for izquierdo, derecho in zip(seleccion, seleccion[1:]):
            if izquierdo != derecho:
                umbrales.append((izquierdo + derecho) / 2.0)
        return umbrales

    def _gini(self, y, indices):
        if not indices:
            return 0.0
        conteo = self._conteo(y, indices)
        total = len(indices)
        return 1.0 - sum((cantidad / total) ** 2 for cantidad in conteo.values())

    @staticmethod
    def _conteo(y, indices):
        conteo = {}
        for i in indices:
            valor = y[i]
            conteo[valor] = conteo.get(valor, 0) + 1
        return conteo

    def _mayoria(self, conteo):
        orden = self.clases or list(conteo.keys())
        mejor = None
        mejor_cantidad = -1
        for clase in orden:
            cantidad = conteo.get(clase, 0)
            if cantidad > mejor_cantidad:
                mejor = clase
                mejor_cantidad = cantidad
        return mejor

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

    # ---------------------------------------------------------------- #
    # Representación legible
    # ---------------------------------------------------------------- #

    def _texto_nodo(self, nodo, sangria):
        prefijo = " " * sangria
        if nodo.es_hoja:
            return [
                "{0}-> {1} (n={2}, {3})".format(
                    prefijo, _texto(nodo.clase), nodo.total, _conteo_texto(nodo.conteo)
                )
            ]
        nombre = self.preprocesador.nombres_features[nodo.indice]
        lineas = [
            "{0}si {1} <= {2}:".format(
                prefijo, nombre, formatear_numero(nodo.umbral)
            )
        ]
        lineas.extend(self._texto_nodo(nodo.izquierda, sangria + 2))
        lineas.append("{0}sino:".format(prefijo))
        lineas.extend(self._texto_nodo(nodo.derecha, sangria + 2))
        return lineas


def _texto(valor):
    if isinstance(valor, bool):
        return "obvio" if valor else "falso"
    return str(valor)


def _conteo_texto(conteo):
    return ", ".join(
        "{0}={1}".format(_texto(clase), cantidad)
        for clase, cantidad in conteo.items()
    )
