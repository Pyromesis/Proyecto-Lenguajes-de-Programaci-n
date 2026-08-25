"""
AREPA - Pruebas de la estructura del árbol de análisis (Fase 1)
---------------------------------------------------------------
Verifica que el árbol producido por ANTLR4:
  * contiene las reglas relevantes de cada instrucción;
  * respeta la jerarquía documentada;
  * codifica la precedencia y asociatividad declaradas
    (o < y < no < comparación < +- < */% < ^ derecha < - unario).

No basta con que el árbol se imprima: aquí se recorre programáticamente.

Uso:
    python pruebas/test_arbol.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from antlr4 import TerminalNode  # noqa: E402

from lenguaje.analizador import analizar  # noqa: E402

CASOS = []
_parser_actual = None


def caso(funcion):
    CASOS.append(funcion)
    return funcion


# ---------------------------------------------------------------------- #
# Utilidades de recorrido propio del árbol
# ---------------------------------------------------------------------- #

def arbol_de(programa):
    """Parsea un programa válido y devuelve (arbol, parser) sin errores."""
    global _parser_actual
    parser, arbol, errores = analizar(programa)
    assert not errores, "el programa debería parsear sin errores: {0}".format(errores)
    _parser_actual = parser
    return arbol, parser


def reglas_en(arbol, parser):
    """Nombres de todas las reglas presentes en el árbol (sin repetir)."""
    encontradas = set()
    pila = [arbol]
    while pila:
        nodo = pila.pop()
        if not isinstance(nodo, TerminalNode):
            encontradas.add(parser.ruleNames[nodo.getRuleIndex()])
            pila.extend(nodo.getChild(i) for i in range(nodo.getChildCount()))
    return encontradas


def nodos_de(arbol, parser, regla):
    """Todos los nodos cuya regla se llame 'regla', en orden del documento."""
    hallados = []

    def visitar(nodo):
        if isinstance(nodo, TerminalNode):
            return
        if parser.ruleNames[nodo.getRuleIndex()] == regla:
            hallados.append(nodo)
        for i in range(nodo.getChildCount()):
            visitar(nodo.getChild(i))

    visitar(arbol)
    return hallados


def hijos_regla(nodo, parser):
    """Reglas de los hijos directos (ignora terminales)."""
    return [
        parser.ruleNames[h.getRuleIndex()]
        for h in (nodo.getChild(i) for i in range(nodo.getChildCount()))
        if not isinstance(h, TerminalNode)
    ]


def hijos_terminal(nodo):
    """Textos de los hijos terminales directos."""
    return [
        h.getText()
        for h in (nodo.getChild(i) for i in range(nodo.getChildCount()))
        if isinstance(h, TerminalNode)
    ]


def profundidad_de(arbol, parser, regla, texto_hoja):
    """Profundidad del ancestro 'regla' más cercano que contiene la hoja."""
    def buscar(nodo, profundidad):
        if isinstance(nodo, TerminalNode):
            return None
        nombre = parser.ruleNames[nodo.getRuleIndex()]
        for i in range(nodo.getChildCount()):
            hijo = nodo.getChild(i)
            if isinstance(hijo, TerminalNode) and hijo.getText() == texto_hoja:
                return profundidad
        for i in range(nodo.getChildCount()):
            hallado = buscar(nodo.getChild(i), profundidad + 1)
            if hallado is not None:
                return profundidad if nombre == regla else hallado
        return None
    return buscar(arbol, 0)


# ---------------------------------------------------------------------- #
# Casos: presencia de reglas por instrucción
# ---------------------------------------------------------------------- #

@caso
def arbol_programa_minimo():
    arbol, parser = arbol_de("quihubo\nchao\n")
    presentes = reglas_en(arbol, parser)
    assert "programa" in presentes
    assert "sentencias" not in presentes  # sin sentencias no aparece


@caso
def arbol_de_asignacion():
    arbol, parser = arbol_de("quihubo\nx = 1 + 2\nchao\n")
    presentes = reglas_en(arbol, parser)
    for regla in ("sentencias", "sentencia", "asignacion", "expresion",
                  "expresion_logica", "comparacion", "aritmetica"):
        assert regla in presentes, "falta la regla {0}".format(regla)
    asignaciones = nodos_de(arbol, parser, "asignacion")
    assert hijos_regla(asignaciones[0], parser) == ["identificador", "expresion"]


@caso
def arbol_de_expresion_aritmetica():
    arbol, parser = arbol_de("quihubo\nx = 2 * 3 + 4\nchao\n")
    assert "termino" in reglas_en(arbol, parser)
    assert "factor" in reglas_en(arbol, parser)


@caso
def arbol_de_comparacion_y_logicos():
    arbol, parser = arbol_de('quihubo\nr = t |> deje donde a > 1 y b == 2\nchao\n')
    presentes = reglas_en(arbol, parser)
    for regla in ("expresion_logica", "conjuncion", "negacion",
                  "comparacion", "operador_relacional"):
        assert regla in presentes, "falta la regla {0}".format(regla)


@caso
def arbol_de_seleccion():
    arbol, parser = arbol_de("quihubo\nr = t |> escoja [a, b]\nchao\n")
    seleccion = nodos_de(arbol, parser, "operacion_datos")[0]
    assert "escoja" in hijos_terminal(seleccion)
    assert "lista_columnas" in hijos_regla(seleccion, parser)


@caso
def arbol_de_filtro():
    arbol, parser = arbol_de("quihubo\nr = t |> deje donde x > 0\nchao\n")
    filtro = nodos_de(arbol, parser, "operacion_datos")[0]
    assert "deje" in hijos_terminal(filtro)
    assert "donde" in hijos_terminal(filtro)
    assert "expresion_logica" in hijos_regla(filtro, parser)


@caso
def arbol_de_visualizacion():
    programa = (
        "quihubo\nt = monte \"a.csv\"\n"
        "pinte barras t\ntitulo \"T\"\nejex x\nmuestrela\nchao\n"
    )
    arbol, parser = arbol_de(programa)
    grafica = nodos_de(arbol, parser, "instruccion_grafica")[0]
    assert "tipo_grafica" in hijos_regla(grafica, parser)
    clausulas = nodos_de(arbol, parser, "clausula_estetica")
    assert len(clausulas) == 2  # titulo y ejex
    assert "final_grafica" in reglas_en(arbol, parser)


@caso
def arbol_de_carga_csv():
    arbol, parser = arbol_de('quihubo\nv = monte "d.csv" con encabezado\nchao\n')
    monte = nodos_de(arbol, parser, "instruccion_monte")[0]
    assert "cadena" in hijos_regla(monte, parser)
    assert "opciones_archivo" in hijos_regla(monte, parser)


@caso
def arbol_de_pipeline_con_etapas():
    programa = (
        'quihubo\nv = monte "d.csv"\n'
        "r = v |> escoja [a] |> deje donde a > 0\nchao\n"
    )
    arbol, parser = arbol_de(programa)
    expresiones = nodos_de(arbol, parser, "expresion")
    assert len(expresiones) == 2  # la de monte y la del pipeline
    etapas = nodos_de(arbol, parser, "etapa_pipeline")
    # pipeline: v, escoja, deje = 3 etapas; monte solo = 1
    assert len(etapas) == 4


# ---------------------------------------------------------------------- #
# Casos: precedencia y asociatividad codificadas en la forma del árbol
# ---------------------------------------------------------------------- #

@caso
def precedencia_multiplicacion_mas_profunda_que_suma():
    arbol, parser = arbol_de("quihubo\nx = 1 + 2 * 3\nchao\n")
    aritmeticas = nodos_de(arbol, parser, "aritmetica")
    raiz = aritmeticas[0]
    assert hijos_terminal(raiz) == ["+"]
    assert hijos_regla(raiz, parser) == ["termino", "termino"]
    # el '*' vive DENTRO del segundo termino, no al nivel del '+'
    segundo = raiz.getChild(2)
    assert "*" in hijos_terminal(segundo.getChild(0)) or _contiene_token(segundo, "*")
    assert "+" not in hijos_terminal(segundo)


@caso
def precedencia_suma_al_mismo_nivel():
    arbol, parser = arbol_de("quihubo\nx = 1 + 2 + 3\nchao\n")
    raiz = nodos_de(arbol, parser, "aritmetica")[0]
    assert hijos_terminal(raiz) == ["+", "+"]
    assert hijos_regla(raiz, parser) == ["termino", "termino", "termino"]


@caso
def precedencia_multiplicacion_primero():
    # a * b + c: la raíz aritmética es '+'; el '*' queda en el primer termino
    arbol, parser = arbol_de("quihubo\nx = 2 * 3 + 4\nchao\n")
    raiz = nodos_de(arbol, parser, "aritmetica")[0]
    assert hijos_terminal(raiz) == ["+"]
    primer_termino = raiz.getChild(0)
    assert "*" in hijos_terminal(primer_termino)


@caso
def precedencia_division_y_suma():
    # a / b + c: igual que el anterior pero con '/'
    arbol, parser = arbol_de("quihubo\nx = 8 / 2 + 1\nchao\n")
    raiz = nodos_de(arbol, parser, "aritmetica")[0]
    assert hijos_terminal(raiz) == ["+"]
    primer_termino = raiz.getChild(0)
    assert "/" in hijos_terminal(primer_termino)


@caso
def comparacion_sobre_la_suma_completa():
    # a + b == c: el '==' compara las dos aritmeticas completas
    arbol, parser = arbol_de("quihubo\nr = t |> deje donde a + b == c\nchao\n")
    filtro = nodos_de(arbol, parser, "operacion_datos")[0]
    condicion = nodos_de(filtro, parser, "expresion_logica")[0]
    comparaciones = [n for n in nodos_de(condicion, parser, "comparacion")
                     if _contiene_token(n, "==")]
    assert len(comparaciones) == 1
    assert hijos_regla(comparaciones[0], parser) == [
        "aritmetica", "operador_relacional", "aritmetica"
    ]
    # el '+' vive dentro de la primera aritmetica, no al nivel del '=='
    assert "+" in hijos_terminal(comparaciones[0].getChild(0))


@caso
def parentesis_con_multiplicacion_dentro():
    # a + (b * c): el '+' manda arriba; el '*' vive dentro del paréntesis
    arbol, parser = arbol_de("quihubo\nx = 1 + (2 * 3)\nchao\n")
    raiz = nodos_de(arbol, parser, "aritmetica")[0]
    assert hijos_terminal(raiz) == ["+"]
    segundo = raiz.getChild(2)
    assert "*" in hijos_terminal(segundo) or _contiene_token(segundo, "*")


@caso
def potencia_asociativa_a_derecha_en_arbol():
    arbol, parser = arbol_de("quihubo\nx = 2 ^ 3 ^ 2\nchao\n")
    factor = nodos_de(arbol, parser, "factor")[0]
    assert hijos_terminal(factor) == ["^"]
    # el segundo '^' está dentro del factor hijo (derecha), no en la raíz
    assert len(nodos_de(factor, parser, "factor")) >= 2


@caso
def logicos_menos_pegajosos_que_comparaciones():
    arbol, parser = arbol_de("quihubo\nr = t |> deje donde a > 1 y b > 2\nchao\n")
    filtro = nodos_de(arbol, parser, "operacion_datos")[0]
    condicion = nodos_de(filtro, parser, "expresion_logica")[0]
    # dentro de la condicion: una sola conjuncion con 'y' arriba y dos
    # comparaciones colgando de negaciones, por debajo del 'y'
    conjunciones = nodos_de(condicion, parser, "conjuncion")
    raiz = conjunciones[0]
    assert hijos_terminal(raiz) == ["y"]
    assert len(nodos_de(condicion, parser, "comparacion")) == 2


@caso
def negacion_aplica_sobre_toda_la_comparacion():
    arbol, parser = arbol_de("quihubo\nr = t |> deje donde no a > 1\nchao\n")
    filtro = nodos_de(arbol, parser, "operacion_datos")[0]
    condicion = nodos_de(filtro, parser, "expresion_logica")[0]
    # la negacion raiz es la que tiene el 'no'; debajo hay una comparacion
    negaciones = [n for n in nodos_de(condicion, parser, "negacion")
                  if "no" in hijos_terminal(n)]
    assert len(negaciones) == 1
    raiz = negaciones[0]
    assert hijos_regla(raiz, parser) == ["negacion"]
    assert len(nodos_de(raiz, parser, "comparacion")) == 1


@caso
def parentesis_alteran_la_estructura():
    arbol_sin, parser = arbol_de("quihubo\nx = 1 + 2 * 3\nchao\n")
    arbol_con, _ = arbol_de("quihubo\nx = (1 + 2) * 3\nchao\n")
    # sin paréntesis: la operación raíz es '+' (aritmetica)
    raiz_sin = nodos_de(arbol_sin, parser, "aritmetica")[0]
    assert hijos_terminal(raiz_sin) == ["+"]
    # con paréntesis: arriba no hay '+'; la raíz aritmética es un termino
    # y la multiplicación ocurre a nivel de termino
    raiz_con = nodos_de(arbol_con, parser, "aritmetica")[0]
    assert "+" not in hijos_terminal(raiz_con)
    termino_raiz = nodos_de(raiz_con, parser, "termino")[0]
    assert "*" in hijos_terminal(termino_raiz)
    # y el (1 + 2) queda encapsulado como atomo con paréntesis
    atomos = nodos_de(raiz_con, parser, "atomo")
    assert any(hijos_terminal(a) and a.getChild(0).getText() == "(" for a in atomos)


def _contiene_token(nodo, texto):
    pila = [nodo]
    while pila:
        actual = pila.pop()
        if isinstance(actual, TerminalNode):
            if actual.getText() == texto:
                return True
        else:
            pila.extend(actual.getChild(i) for i in range(actual.getChildCount()))
    return False


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE LA ESTRUCTURA DEL ÁRBOL DE ANÁLISIS")
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
