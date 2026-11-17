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
from errores_base import ErrorSemantico
from utiles.matematica import es_finito
from ml.modelo import exigir_numero_finito


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
    y, predicciones = _numericos(y, predicciones)
    escala = max(abs(v) for v in y + predicciones) or 1.0
    return _resultado(sum(abs(a / escala - p / escala) / len(y)
                          for a, p in zip(y, predicciones)) * escala)


def error_cuadratico_medio(y, predicciones):
    _validar(y, predicciones)
    y, predicciones = _numericos(y, predicciones)
    return _resultado(sum(((a - p) * (a - p)) / len(y) for a, p in zip(y, predicciones)))


def raiz_error_cuadratico(y, predicciones):
    _validar(y, predicciones)
    y, predicciones = _numericos(y, predicciones)
    escala = max(abs(v) for v in y + predicciones) or 1.0
    normalizado = sum((a / escala - p / escala) ** 2 / len(y)
                      for a, p in zip(y, predicciones))
    return _resultado((normalizado ** 0.5) * escala)


def coeficiente_determinacion(y, predicciones):
    """R² = 1 - suma(errores²) / suma((y - media)²)."""
    _validar(y, predicciones)
    y, predicciones = _numericos(y, predicciones)
    escala = max(abs(v) for v in y + predicciones) or 1.0
    y = [v / escala for v in y]
    predicciones = [v / escala for v in predicciones]
    media = sum(a / len(y) for a in y)
    total = sum((a - media) ** 2 for a in y)
    residual = sum((a - p) ** 2 for a, p in zip(y, predicciones))
    if total == 0:
        return 1.0 if residual == 0 else 0.0
    return _resultado(1.0 - residual / total)


def _numericos(y, predicciones):
    return ([exigir_numero_finito(v, "valor real de evaluación") for v in y],
            [exigir_numero_finito(v, "predicción de evaluación") for v in predicciones])


def _resultado(valor):
    if not es_finito(valor):
        raise ErrorSemantico("La métrica excede el rango decimal; revisá la "
                             "escala de los datos y las predicciones. No se informa NaN como resultado válido.")
    return valor


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
