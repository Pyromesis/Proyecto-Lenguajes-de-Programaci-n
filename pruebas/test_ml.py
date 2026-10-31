"""
AREPA - Pruebas de la biblioteca propia de machine learning (src/ml)
-------------------------------------------------------------------
Verifica, sin sklearn/numpy/pandas, el preprocesamiento, las métricas,
la regresión lineal, el perceptrón, el árbol de decisión y su integración
con el runtime del DSL ('entrene', 'prediga', 'clasifique', 'evalua').

Uso:
    python3 pruebas/test_ml.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.fila import Fila  # noqa: E402
from datos.tabla import Tabla  # noqa: E402
from datos.tipos import NADA, nombre_tipo  # noqa: E402
from errores_base import ErrorArepa, ErrorSemantico  # noqa: E402
from lenguaje.analizador import analizar  # noqa: E402
from ml import metricas  # noqa: E402
from ml.arbol_decision import ArbolDecision  # noqa: E402
from ml.perceptron import Perceptron  # noqa: E402
from ml.preprocesamiento import Preprocesador  # noqa: E402
from ml.regresion_lineal import RegresionLineal  # noqa: E402
from runtime.contexto import a_texto  # noqa: E402
from runtime.ejecutor import EjecutorArepa  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


def correr(programa):
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa no parseó: {0}".format(errores)
    ejecutor = EjecutorArepa()
    ejecutor.ejecutar(arbol)
    return ejecutor


def correr_y_fallar(programa):
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa debería fallar en ejecución, no en parseo"
    try:
        EjecutorArepa().ejecutar(arbol)
    except ErrorArepa as problema:
        return problema
    raise AssertionError("el programa debería haber fallado: " + programa)


def _tabla(nombres, filas, nombre="t"):
    return Tabla(nombres, [Fila(fila) for fila in filas], nombre=nombre)


def _ruta(nombre):
    carpeta = os.path.join(RAIZ, "salidas")
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    return os.path.join(carpeta, nombre).replace("\\", "/")


def _escribir(nombre, contenido):
    ruta = _ruta(nombre)
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(contenido)
    return ruta


def _tabla_estudiantes():
    return _tabla(
        ["horas", "asistencia", "aprueba"],
        [
            [1, 50, "no"],
            [1.5, 55, "no"],
            [2, 60, "no"],
            [3, 75, "si"],
            [3.5, 80, "si"],
            [4, 90, "si"],
        ],
    )


def _tabla_riesgo():
    return _tabla(
        ["edad", "deuda", "riesgo"],
        [
            [20, 9000, "alto"],
            [22, 8000, "alto"],
            [25, 7000, "alto"],
            [35, 4000, "medio"],
            [38, 3500, "medio"],
            [40, 3000, "medio"],
            [55, 1000, "bajo"],
            [60, 800, "bajo"],
            [65, 500, "bajo"],
        ],
    )


def _profundidad(nodo):
    if nodo.es_hoja:
        return 0
    return 1 + max(_profundidad(nodo.izquierda), _profundidad(nodo.derecha))


# ---------------------------------------------------------------------- #
# Preprocesamiento
# ---------------------------------------------------------------------- #

@caso
def preprocesador_imputa_media_y_moda():
    tabla = _tabla(
        ["x1", "x2", "ciudad", "y"],
        [
            [1, 10, "A", 5],
            [2, NADA, "B", 7],
            [3, 30, "A", 9],
            [4, 40, NADA, 11],
        ],
    )
    pre = Preprocesador(tabla, ["x1", "x2", "ciudad"], "y")
    vector = pre.transformar_fila(tabla.filas[1], tabla)
    assert vector[0] == 2.0
    assert abs(vector[1] - 26.666666666666668) < 1e-9
    assert vector[2:] == [0.0, 1.0]  # ciudad B -> one-hot [A, B]


@caso
def preprocesador_nombres_one_hot():
    tabla = _tabla(["ciudad", "y"], [["A", 1], ["B", 2], ["A", 3]])
    pre = Preprocesador(tabla, ["ciudad"], "y")
    assert pre.nombres_features == ["ciudad=A", "ciudad=B"]
    assert pre.dimension == 2


@caso
def preprocesador_descarta_objetivo_vacio():
    tabla = _tabla(["x", "y"], [[1, 2], [2, NADA], [3, 6]])
    pre = Preprocesador(tabla, ["x"], "y")
    X, y = pre.datos(tabla)
    assert len(X) == 2 and y == [2, 6]


@caso
def preprocesador_rechaza_objetivo_en_columnas():
    tabla = _tabla(["x", "y"], [[1, 2]])
    try:
        Preprocesador(tabla, ["x", "y"], "y")
        raise AssertionError("el objetivo no puede ser también una entrada")
    except ErrorSemantico as problema:
        assert "respuesta" in problema.mensaje


@caso
def preprocesador_rechaza_columna_inexistente():
    tabla = _tabla(["x", "y"], [[1, 2]])
    try:
        Preprocesador(tabla, ["z"], "y")
        raise AssertionError("la columna z no existe")
    except ErrorArepa as problema:
        assert "z" in str(problema)


# ---------------------------------------------------------------------- #
# Métricas
# ---------------------------------------------------------------------- #

@caso
def metricas_regresion_conocidas():
    y = [3, 5, 7]
    p = [2, 5, 9]
    assert metricas.error_absoluto_medio(y, p) == 1.0
    assert abs(metricas.error_cuadratico_medio(y, p) - 5.0 / 3.0) < 1e-12
    assert abs(metricas.raiz_error_cuadratico(y, p) - (5.0 / 3.0) ** 0.5) < 1e-12
    assert abs(metricas.coeficiente_determinacion(y, p) - 0.375) < 1e-12


@caso
def metricas_clasificacion_matriz():
    y = ["a", "a", "b", "b"]
    p = ["a", "b", "b", "b"]
    clases, matriz = metricas.matriz_confusion(y, p)
    assert clases == ["a", "b"]
    assert matriz == [[1, 1], [0, 2]]
    assert metricas.exactitud(y, p) == 0.75


@caso
def metricas_por_clase_precision_recall_f1():
    y = ["a", "a", "b", "b"]
    p = ["a", "b", "b", "b"]
    por_clase = {d["clase"]: d for d in metricas.metricas_por_clase(y, p)}
    assert por_clase["a"]["precision"] == 1.0
    assert por_clase["a"]["recall"] == 0.5
    assert abs(por_clase["a"]["f1"] - 2.0 / 3.0) < 1e-12
    assert abs(por_clase["b"]["precision"] - 2.0 / 3.0) < 1e-12


@caso
def metricas_rechazan_listas_vacias():
    try:
        metricas.exactitud([], [])
        raise AssertionError("no se pueden calcular métricas sin datos")
    except ValueError as problema:
        assert "datos" in str(problema)


# ---------------------------------------------------------------------- #
# Modelos
# ---------------------------------------------------------------------- #

@caso
def regresion_aprende_relacion_lineal():
    tabla = _tabla(
        ["x", "y"], [[i, 2 * i + 3] for i in range(1, 21)], nombre="lineal"
    )
    pre = Preprocesador(tabla, ["x"], "y")
    X, y = pre.datos(tabla, estandarizar=True)
    modelo = RegresionLineal(pre, "y", tasa=0.1, epocas=4000)
    modelo.entrenar(X, y)
    predicciones = [modelo.predecir(fila) for fila in X]
    r2 = metricas.coeficiente_determinacion(y, predicciones)
    assert r2 > 0.99, "R² fue {0}".format(r2)
    assert abs(modelo.sesgo - 24.0) < 0.5


@caso
def regresion_rechaza_hiperparametros_y_objetivo_invalidos():
    tabla = _tabla(["x", "y"], [[1, 2], [2, 4]])
    pre = Preprocesador(tabla, ["x"], "y")
    try:
        RegresionLineal(pre, "y", tasa=0)
        raise AssertionError("la tasa debe ser mayor que 0")
    except ErrorSemantico as problema:
        assert "tasa" in problema.mensaje

    # Un objetivo de texto no se puede sumar: debe dar un error semántico
    # claro y no un TypeError de Python.
    modelo = RegresionLineal(pre, "y")
    try:
        modelo.entrenar([[1.0], [2.0]], ["alto", "bajo"])
        raise AssertionError("la regresión necesita un objetivo numérico")
    except ErrorSemantico as problema:
        assert "objetivo numérico" in problema.mensaje


@caso
def perceptron_separa_dos_clases():
    tabla = _tabla(
        ["x1", "x2", "clase"],
        [
            [1, 1, "A"], [1, 2, "A"], [2, 1, "A"], [2, 2, "A"],
            [8, 8, "B"], [8, 9, "B"], [9, 8, "B"], [9, 9, "B"],
        ],
    )
    pre = Preprocesador(tabla, ["x1", "x2"], "clase")
    X, y = pre.datos(tabla, estandarizar=True)
    modelo = Perceptron(pre, "clase", tasa=0.1, epocas=100, clases=["A", "B"])
    modelo.entrenar(X, y)
    predicciones = [modelo.predecir(fila) for fila in X]
    assert predicciones == y
    assert modelo.historial[-1] == 0


@caso
def perceptron_es_binario():
    tabla = _tabla(
        ["x", "clase"], [[1, "A"], [2, "B"], [3, "C"]]
    )
    pre = Preprocesador(tabla, ["x"], "clase")
    X, y = pre.datos(tabla, estandarizar=True)
    modelo = Perceptron(pre, "clase")
    try:
        modelo.entrenar(X, y)
        raise AssertionError("el perceptrón no admite 3 clases")
    except ErrorSemantico as problema:
        assert "binario" in problema.mensaje


@caso
def perceptron_respeta_orden_de_clases():
    tabla = _tabla(
        ["x", "clase"], [[1, "A"], [2, "A"], [8, "B"], [9, "B"]]
    )
    pre = Preprocesador(tabla, ["x"], "clase")
    X, y = pre.datos(tabla, estandarizar=True)
    modelo = Perceptron(pre, "clase", clases=["B", "A"])
    modelo.entrenar(X, y)
    assert modelo.clases == ["B", "A"]
    assert modelo.predecir(pre.transformar_fila(tabla.filas[2], tabla, True)) == "B"


@caso
def arbol_clasifica_multiclase():
    tabla = _tabla_riesgo()
    pre = Preprocesador(tabla, ["edad", "deuda"], "riesgo")
    X, y = pre.datos(tabla)
    modelo = ArbolDecision(pre, "riesgo", profundidad=5)
    modelo.entrenar(X, y)
    assert [modelo.predecir(fila) for fila in X] == y
    assert modelo.exactitud_entrenamiento == 1.0


@caso
def arbol_respeta_profundidad_maxima():
    tabla = _tabla_riesgo()
    pre = Preprocesador(tabla, ["edad", "deuda"], "riesgo")
    X, y = pre.datos(tabla)
    modelo = ArbolDecision(pre, "riesgo", profundidad=2)
    modelo.entrenar(X, y)
    assert _profundidad(modelo.raiz) <= 2


@caso
def arbol_min_hojas_evita_division():
    tabla = _tabla_riesgo()
    pre = Preprocesador(tabla, ["edad", "deuda"], "riesgo")
    X, y = pre.datos(tabla)
    modelo = ArbolDecision(pre, "riesgo", min_hojas=100)
    modelo.entrenar(X, y)
    assert modelo.raiz.es_hoja


@caso
def modelos_declaran_su_tipo_arepa():
    tabla = _tabla(["x", "y"], [[1, 2], [2, 4]])
    pre = Preprocesador(tabla, ["x"], "y")
    regresion = RegresionLineal(pre, "y")
    arbol = ArbolDecision(pre, "y")
    assert nombre_tipo(regresion) == "regresion"
    assert nombre_tipo(arbol) == "clasificacion"


@caso
def a_texto_muestra_resumen_del_modelo():
    tabla = _tabla(["x", "y"], [[1, 2], [2, 4]])
    pre = Preprocesador(tabla, ["x"], "y")
    texto = a_texto(RegresionLineal(pre, "y"))
    assert "objetivo: y" in texto
    assert "descenso de gradiente" in texto


# ---------------------------------------------------------------------- #
# Integración con el DSL
# ---------------------------------------------------------------------- #

@caso
def dsl_regresion_prediga_y_guarde():
    ruta = _escribir(
        "prueba_ml_regresion.csv",
        "x,y\n1,5\n2,7\n3,9\n4,11\n5,13\n6,15\n7,17\n8,19\n",
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = regresion con t\n"
        "  columnas [x]\n"
        "  objetivo y\n"
        "  tasa 0.1\n"
        "  epocas 3000\n"
        "r = t |> prediga con m como estimado\n"
        'guarde r como "{1}"\n'
        "chao\n".format(ruta, _ruta("prueba_ml_predicciones.csv"))
    )
    ejecutor = correr(programa)
    tabla = ejecutor.contexto.simbolos.buscar("r")
    assert tabla.nombres_columnas == ["x", "y", "estimado"]
    for fila in tabla.filas:
        assert abs(fila.valor_en(2) - fila.valor_en(1)) < 0.5
    assert os.path.isfile(_ruta("prueba_ml_predicciones.csv"))


@caso
def dsl_perceptron_clasifique():
    ruta = _escribir(
        "prueba_ml_perceptron.csv",
        "x1,x2,clase\n"
        "1,1,A\n1,2,A\n2,1,A\n2,2,A\n"
        "8,8,B\n8,9,B\n9,8,B\n9,9,B\n",
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = perceptron con t\n"
        "  columnas [x1, x2]\n"
        "  objetivo clase\n"
        '  clases ["A", "B"]\n'
        "  tasa 0.1\n"
        "  epocas 100\n"
        "r = t |> clasifique con m como predicha\n"
        "chao\n".format(ruta)
    )
    tabla = correr(programa).contexto.simbolos.buscar("r")
    assert [f.valor_en(3) for f in tabla.filas] == ["A"] * 4 + ["B"] * 4


@caso
def dsl_arbol_clasifique():
    ruta = _escribir(
        "prueba_ml_arbol.csv",
        "edad,deuda,riesgo\n"
        "20,9000,alto\n22,8000,alto\n25,7000,alto\n"
        "35,4000,medio\n38,3500,medio\n40,3000,medio\n"
        "55,1000,bajo\n60,800,bajo\n65,500,bajo\n",
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = arbol con t\n"
        "  columnas [edad, deuda]\n"
        "  objetivo riesgo\n"
        '  clases ["alto", "medio", "bajo"]\n'
        "  profundidad 4\n"
        "  min_hojas 2\n"
        "r = t |> clasifique con m como predicha\n"
        "chao\n".format(ruta)
    )
    tabla = correr(programa).contexto.simbolos.buscar("r")
    assert [f.valor_en(3) for f in tabla.filas] == [
        "alto", "alto", "alto", "medio", "medio", "medio", "bajo", "bajo", "bajo"
    ]


@caso
def dsl_evalua_imprime_metricas():
    ruta = _escribir(
        "prueba_ml_evalua.csv",
        "x,clase\n1,A\n2,A\n8,B\n9,B\n",
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = perceptron con t\n"
        "  columnas [x]\n"
        "  objetivo clase\n"
        "  epocas 100\n"
        "evalua m con t\n"
        "chao\n".format(ruta)
    )
    salida = "\n".join(correr(programa).contexto.salida)
    assert "Métricas de clasificación" in salida
    assert "exactitud = 1" in salida
    assert "Matriz de confusión" in salida


@caso
def dsl_prediga_rechaza_modelo_de_clasificacion():
    ruta = _escribir(
        "prueba_ml_tipos.csv", "x,clase\n1,A\n2,A\n8,B\n9,B\n"
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = perceptron con t\n"
        "  columnas [x]\n"
        "  objetivo clase\n"
        "r = t |> prediga con m como estimado\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "regresión" in problema.mensaje


@caso
def dsl_regresion_rechaza_clases():
    ruta = _escribir("prueba_ml_clases.csv", "x,y\n1,2\n2,4\n")
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = regresion con t\n"
        "  columnas [x]\n"
        "  objetivo y\n"
        '  clases ["si", "no"]\n'
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "no usa 'clases" in problema.mensaje


@caso
def dsl_perceptron_rechaza_profundidad():
    ruta = _escribir(
        "prueba_ml_opciones.csv", "x,clase\n1,A\n2,A\n8,B\n9,B\n"
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = perceptron con t\n"
        "  columnas [x]\n"
        "  objetivo clase\n"
        "  profundidad 3\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "arbol" in problema.mensaje


@caso
def dsl_arbol_rechaza_tasa():
    ruta = _escribir(
        "prueba_ml_opciones2.csv", "x,clase\n1,A\n2,A\n8,B\n9,B\n"
    )
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = arbol con t\n"
        "  columnas [x]\n"
        "  objetivo clase\n"
        "  tasa 0.1\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "tasa" in problema.mensaje


@caso
def dsl_entrene_exige_columnas():
    ruta = _escribir("prueba_ml_sin_columnas.csv", "x,y\n1,2\n2,4\n")
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = regresion con t\n"
        "  objetivo y\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "columnas" in problema.mensaje


@caso
def dsl_entrene_exige_objetivo():
    ruta = _escribir("prueba_ml_sin_objetivo.csv", "x,y\n1,2\n2,4\n")
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "entrene m = regresion con t\n"
        "  columnas [x]\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "objetivo" in problema.mensaje


@caso
def dsl_evalua_modelo_inexistente():
    ruta = _escribir("prueba_ml_inexistente.csv", "x,y\n1,2\n2,4\n")
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "evalua fantasma con t\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "fantasma" in problema.mensaje


@caso
def dsl_prediga_exige_modelo_no_tabla():
    ruta = _escribir("prueba_ml_no_modelo.csv", "x,y\n1,2\n2,4\n")
    programa = (
        "quihubo\n"
        't = monte "{0}" con encabezado\n'
        "r = t |> prediga con t como estimado\n"
        "chao\n".format(ruta)
    )
    problema = correr_y_fallar(programa)
    assert "modelo de machine learning" in problema.mensaje


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE LA BIBLIOTECA PROPIA DE MACHINE LEARNING")
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
