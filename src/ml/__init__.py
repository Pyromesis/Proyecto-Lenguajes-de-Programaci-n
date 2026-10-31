"""
AREPA - Biblioteca propia de machine learning (src/ml)
------------------------------------------------------
Todos los algoritmos están implementados desde cero por el equipo:
preprocesamiento, regresión lineal, perceptrón, árbol de decisión y
métricas. La única dependencia externa del proyecto sigue siendo ANTLR4
para el lexer/parser.
"""

from ml.arbol_decision import ArbolDecision
from ml.modelo import ModeloClasificacion, ModeloML, ModeloRegresion
from ml.perceptron import Perceptron
from ml.preprocesamiento import Preprocesador
from ml.regresion_lineal import RegresionLineal

__all__ = [
    "ArbolDecision",
    "ModeloClasificacion",
    "ModeloML",
    "ModeloRegresion",
    "Perceptron",
    "Preprocesador",
    "RegresionLineal",
]
