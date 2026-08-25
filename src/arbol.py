"""
AREPA - Impresión del árbol de análisis (Fase 1)
------------------------------------------------
Convierte el árbol de análisis generado por ANTLR4 en una
representación jerárquica legible en consola.
"""

from antlr4 import TerminalNode

RAMA_MEDIA = "|-- "
RAMA_ULTIMA = "`-- "
PREFIJO_MEDIO = "|   "
PREFIJO_ULTIMO = "    "

def _es_salto(texto):
    """True si el texto del token consiste solo de caracteres de salto."""
    return len(texto) > 0 and all(c in "\r\n" for c in texto)


def _etiqueta(nodo, parser):
    """Nombre de la regla (nodos internos) o texto del token (hojas)."""
    if isinstance(nodo, TerminalNode):
        texto = nodo.getText()
        if _es_salto(texto):
            return "<salto>"
        return "'{0}'".format(texto)
    indice = nodo.getRuleIndex()
    return parser.ruleNames[indice]


def _hijos_visibles(nodo):
    """Hijos del nodo ocultando los tokens de salto de línea."""
    hijos = []
    for i in range(nodo.getChildCount()):
        hijo = nodo.getChild(i)
        if isinstance(hijo, TerminalNode) and _es_salto(hijo.getText()):
            continue
        hijos.append(hijo)
    return hijos


def imprimir_arbol(arbol, parser):
    """Imprime el árbol de análisis completo en la consola."""
    print("Árbol de análisis:")
    _imprimir_nodo(arbol, parser, "", True)


def _imprimir_nodo(nodo, parser, prefijo, es_ultimo):
    conector = RAMA_ULTIMA if es_ultimo else RAMA_MEDIA
    print(prefijo + conector + _etiqueta(nodo, parser))
    hijos = _hijos_visibles(nodo)
    cantidad = len(hijos)
    if cantidad == 0:
        return
    nuevo_prefijo = prefijo + (PREFIJO_ULTIMO if es_ultimo else PREFIJO_MEDIO)
    for i, hijo in enumerate(hijos):
        _imprimir_nodo(hijo, parser, nuevo_prefijo, i == cantidad - 1)


def contar_sentencias(arbol):
    """Cuenta las sentencias reconocidas bajo la regla 'sentencias'."""
    total = 0
    pila = [arbol]
    while pila:
        actual = pila.pop()
        texto_regla = None
        if not isinstance(actual, TerminalNode):
            texto_regla = actual.parser.ruleNames[actual.getRuleIndex()]
        if texto_regla == "sentencia":
            total += 1
            continue
        for hijo in _hijos_visibles(actual):
            pila.append(hijo)
    return total
