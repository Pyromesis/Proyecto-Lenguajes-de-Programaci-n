"""
AREPA - Métricas propias de machine learning (src/ml/metricas.py)
-----------------------------------------------------------------
Implementado por el equipo desde cero. Calcula las métricas que usa
'Universidad Sergio Arboleda - Lenguajes de Programación' para evaluar
modelos supervisados, sin sklearn ni numpy.

Regresión:
  * error absoluto medio (MAE);
  * error cuadrático medio (MSE);
  * raíz del error cuadrático medio (RMSE);
  * coeficiente de determinación R².

Clasificación:
  * exactitud (accuracy);
  * matriz de confusión;
  * precisión, exhaustividad (recall) y F1 por clase.
"""

from datos.tipos import formatear_numero


def _validar(y, predicciones):
    if len(y) != len(predicciones):
        raise ValueError(
            "Las etiquetas y las predicciones deben tener el mismo tamaño: "
            "{0} vs {1}.".format(len(y), len(predicciones))
        )
    if not y:
        raise ValueError("No hay datos para calcular métricas.")


def error_absoluto_medio(y, predicciones):
    _validar(y, predicciones)
    return sum(abs(a - p) for a, p in zip(y, predicciones)) / len(y)


def error_cuadratico_medio(y, predicciones):
    _validar(y, predicciones)
    return sum((a - p) ** 2 for a, p in zip(y, predicciones)) / len(y)


def raiz_error_cuadratico(y, predicciones):
    return error_cuadratico_medio(y, predicciones) ** 0.5


def coeficiente_determinacion(y, predicciones):
    """R² = 1 - suma(errores²) / suma((y - media)²)."""
    _validar(y, predicciones)
    media = sum(y) / len(y)
    total = sum((a - media) ** 2 for a in y)
    residual = sum((a - p) ** 2 for a, p in zip(y, predicciones))
    if total == 0:
        return 1.0 if residual == 0 else 0.0
    return 1.0 - residual / total


def exactitud(y, predicciones):
    _validar(y, predicciones)
    aciertos = sum(1 for a, p in zip(y, predicciones) if a == p)
    return aciertos / len(y)


def matriz_confusion(y, predicciones, clases=None):
    """Devuelve (clases, matriz) con filas reales y columnas predichas.

    Si se pasa 'clases', ese es el orden de la matriz; las clases que
    aparezcan en los datos y no estén en la lista se agregan al final.
    """
    _validar(y, predicciones)
    orden = []
    vistas = set()
    for valor in list(clases or []) + list(y) + list(predicciones):
        if valor not in vistas:
            vistas.add(valor)
            orden.append(valor)
    posicion = {clase: i for i, clase in enumerate(orden)}
    matriz = [[0 for _ in orden] for _ in orden]
    for real, predicha in zip(y, predicciones):
        matriz[posicion[real]][posicion[predicha]] += 1
    return orden, matriz


def metricas_por_clase(y, predicciones, clases=None):
    """Lista de diccionarios con precisión, recall y F1 por clase."""
    orden, matriz = matriz_confusion(y, predicciones, clases)
    resultado = []
    for i, clase in enumerate(orden):
        verdaderos_positivos = matriz[i][i]
        falsos_positivos = sum(matriz[fila][i] for fila in range(len(orden))) - verdaderos_positivos
        falsos_negativos = sum(matriz[i]) - verdaderos_positivos
        precision = _division(verdaderos_positivos, verdaderos_positivos + falsos_positivos)
        recall = _division(verdaderos_positivos, verdaderos_positivos + falsos_negativos)
        f1 = _division(2 * precision * recall, precision + recall)
        resultado.append(
            {
                "clase": clase,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "soporte": sum(matriz[i]),
            }
        )
    return resultado


def resumen_regresion(y, predicciones):
    lineas = [
        "Métricas de regresión ({0} filas):".format(len(y)),
        "  MAE  = {0}".format(_num(error_absoluto_medio(y, predicciones))),
        "  MSE  = {0}".format(_num(error_cuadratico_medio(y, predicciones))),
        "  RMSE = {0}".format(_num(raiz_error_cuadratico(y, predicciones))),
        "  R²   = {0}".format(_num(coeficiente_determinacion(y, predicciones))),
    ]
    return "\n".join(lineas)


def resumen_clasificacion(y, predicciones, clases=None):
    orden, matriz = matriz_confusion(y, predicciones, clases)
    lineas = [
        "Métricas de clasificación ({0} filas):".format(len(y)),
        "  exactitud = {0}".format(_num(exactitud(y, predicciones))),
        "",
        "  Matriz de confusión (filas = real, columnas = predicho):",
    ]
    ancho = max([len(_texto(c)) for c in orden] + [7])
    encabezado = " " * (ancho + 2) + " ".join(_texto(c).rjust(ancho) for c in orden)
    lineas.append(encabezado)
    for i, clase in enumerate(orden):
        fila = "  " + _texto(clase).ljust(ancho) + " " + " ".join(
            str(valor).rjust(ancho) for valor in matriz[i]
        )
        lineas.append(fila)
    lineas.append("")
    lineas.append("  Por clase:")
    for datos in metricas_por_clase(y, predicciones, clases):
        lineas.append(
            "    {0}: precisión={1}, recall={2}, F1={3}, soporte={4}".format(
                _texto(datos["clase"]),
                _num(datos["precision"]),
                _num(datos["recall"]),
                _num(datos["f1"]),
                datos["soporte"],
            )
        )
    return "\n".join(lineas)


def _division(numerador, denominador):
    return numerador / denominador if denominador else 0.0


def _num(valor):
    return formatear_numero(valor)


def _texto(valor):
    if isinstance(valor, bool):
        return "obvio" if valor else "falso"
    return str(valor)
