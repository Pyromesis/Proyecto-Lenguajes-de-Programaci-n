"""
AREPA - Evaluador de expresiones propio (src/expresiones/evaluador.py)
----------------------------------------------------------------------
Implementado por el equipo. Recorre el arbol de analisis que produce
ANTLR4 (uso autorizado) y calcula el valor de cada expresion del DSL
con los operadores propios de expresiones/operadores.py.

No se usa eval() ni exec() ni ningun motor externo: la precedencia ya
quedo codificada en la estructura del arbol y aqui solo se recorre.

Resolucion de nombres (en este orden):
  1. si hay una fila en contexto y el nombre es columna de esa tabla,
     devuelve el valor de la celda;
  2. si es una variable declarada, devuelve su valor;
  3. si no, lanza ErrorVariable con las columnas disponibles como pista.

Modo especial 'modo_columna': durante las agregaciones de 'resuma' los
argumentos son nombres de columnas, no valores; con esta bandera el
nombre se devuelve tal cual.

Limitaciones:
  * la ubicacion (linea/columna) de un error de tipos es aproximada:
    se reporta la posicion donde inicia la expresion.
"""

from datos.tipos import NADA
from errores_base import ErrorArepa, ErrorVariable
from expresiones import operadores as ops

from ArepaVisitor import ArepaVisitor

OPERADORES_RELACIONALES = {
    "==": ops.igual,
    "!=": ops.diferente,
    "<": ops.menor,
    "<=": ops.menor_igual,
    ">": ops.mayor,
    ">=": ops.mayor_igual,
}

OPERADORES_ARITMETICOS = {
    "+": ops.sumar,
    "-": ops.restar,
    "*": ops.multiplicar,
    "/": ops.dividir,
    "%": ops.modulo,
}

# Agregaciones del lenguaje: sus argumentos son NOMBRES de columnas, no
# valores, así que se evalúan siempre en modo columna.
AGREGACIONES = (
    "cuente", "sume", "promedie", "mediana", "minimo", "maximo", "desviacion",
)


class EvaluadorExpresiones(ArepaVisitor):
    """Calcula el valor de las expresiones del DSL sobre su arbol."""

    def __init__(self, simbolos, invocar=None):
        super().__init__()
        self.simbolos = simbolos
        self.invocar = invocar
        self._fila = None
        self._tabla = None
        self.modo_columna = False

    # ---------------------------------------------------------------- #
    # Punto de entrada
    # ---------------------------------------------------------------- #

    def evaluar(self, ctx, fila=None, tabla=None):
        """Evalua un nodo de expresion con una fila opcional en contexto.

        Si un error propio se lanza sin ubicacion, se completa con la
        posicion del nodo que inicio la evaluacion (aproximacion).
        """
        fila_previa, tabla_previa = self._fila, self._tabla
        self._fila, self._tabla = fila, tabla
        try:
            return self.visit(ctx)
        except ErrorArepa as problema:
            if problema.linea == -1 and ctx.start is not None:
                problema.linea = ctx.start.line
                problema.columna = ctx.start.column
            raise
        finally:
            self._fila, self._tabla = fila_previa, tabla_previa

    # ---------------------------------------------------------------- #
    # Logica: o < y < no
    # ---------------------------------------------------------------- #

    def visitExpresion_logica(self, ctx):
        valor = self.visit(ctx.conjuncion(0))
        for i in range(1, len(ctx.conjuncion())):
            valor = ops.disyuncion(valor, self.visit(ctx.conjuncion(i)))
        return valor

    def visitConjuncion(self, ctx):
        valor = self.visit(ctx.negacion(0))
        for i in range(1, len(ctx.negacion())):
            valor = ops.conjuncion(valor, self.visit(ctx.negacion(i)))
        return valor

    def visitNegacion(self, ctx):
        if ctx.NO() is not None:
            return ops.negar_logico(self.visit(ctx.negacion()))
        return self.visit(ctx.comparacion())

    # ---------------------------------------------------------------- #
    # Comparaciones
    # ---------------------------------------------------------------- #

    def visitComparacion(self, ctx):
        izquierda = self.visit(ctx.aritmetica(0))
        relacional = ctx.operador_relacional()
        if relacional is None:
            return izquierda
        operacion = OPERADORES_RELACIONALES[relacional.getText()]
        return operacion(izquierda, self.visit(ctx.aritmetica(1)))

    # ---------------------------------------------------------------- #
    # Aritmetica: +- < */% < ^ (asociativa a derecha) < - unario
    # ---------------------------------------------------------------- #

    def visitAritmetica(self, ctx):
        valor = self.visit(ctx.termino(0))
        for i in range(1, len(ctx.termino())):
            operador = ctx.getChild(2 * i - 1).getText()
            valor = OPERADORES_ARITMETICOS[operador](valor, self.visit(ctx.termino(i)))
        return valor

    def visitTermino(self, ctx):
        valor = self.visit(ctx.factor(0))
        for i in range(1, len(ctx.factor())):
            operador = ctx.getChild(2 * i - 1).getText()
            valor = OPERADORES_ARITMETICOS[operador](valor, self.visit(ctx.factor(i)))
        return valor

    def visitFactor(self, ctx):
        base = self.visit(ctx.unario())
        if ctx.POTENCIA() is not None:
            return ops.potenciar(base, self.visit(ctx.factor()))
        return base

    def visitUnario(self, ctx):
        if ctx.MENOS() is not None:
            return ops.negar_numero(self.visit(ctx.unario()))
        return self.visit(ctx.atomo())

    # ---------------------------------------------------------------- #
    # Atomos y literales
    # ---------------------------------------------------------------- #

    def visitAtomo(self, ctx):
        if ctx.ENTERO() is not None:
            return int(ctx.getText())
        if ctx.DECIMAL() is not None:
            return float(ctx.getText())
        if ctx.cadena() is not None:
            return self.visit(ctx.cadena())
        if ctx.OBVIO() is not None:
            return True
        if ctx.FALSO() is not None:
            return False
        if ctx.NADA() is not None:
            return NADA
        if ctx.llamada_funcion() is not None:
            return self.visit(ctx.llamada_funcion())
        if ctx.nombre_columna() is not None:
            return self._resolver_nombre(ctx.nombre_columna())
        return self.visit(ctx.expresion())

    def visitCadena(self, ctx):
        cruda = ctx.getText()
        return self._desescapar(cruda[1:-1])

    @staticmethod
    def _desescapar(texto):
        """Convierte los escapes \\n \\t \\r \\\" \\\\ a sus caracteres."""
        resultado = []
        i = 0
        while i < len(texto):
            caracter = texto[i]
            if caracter == "\\" and i + 1 < len(texto):
                siguiente = texto[i + 1]
                mapa = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
                if siguiente in mapa:
                    resultado.append(mapa[siguiente])
                    i += 2
                    continue
            resultado.append(caracter)
            i += 1
        return "".join(resultado)

    # ---------------------------------------------------------------- #
    # Nombres: columna de la fila actual o variable declarada
    # ---------------------------------------------------------------- #

    def _resolver_nombre(self, ctx_nombre):
        nombre = ctx_nombre.getText()
        if self.modo_columna:
            return nombre
        if self._tabla is not None and self._fila is not None:
            if self._tabla.tiene_columna(nombre):
                indice = self._tabla._indice_opcional(nombre)
                return self._fila.valor_en(indice)
        if self.simbolos.existe(nombre):
            return self.simbolos.buscar(nombre)
        pistas = ""
        if self._tabla is not None:
            pistas = " Columnas disponibles: {0}.".format(
                ", ".join(self._tabla.nombres_columnas)
            )
        raise ErrorVariable(
            "El nombre '{0}' no existe ni como columna ni como variable.{1}".format(
                nombre, pistas
            ),
            linea=ctx_nombre.start.line,
            columna=ctx_nombre.start.column,
        )

    # ---------------------------------------------------------------- #
    # Llamadas a funciones: las resuelve el ejecutor mediante el
    # callback 'invocar' (funciones del usuario y agregaciones).
    # ---------------------------------------------------------------- #

    def visitLlamada_funcion(self, ctx):
        nombre = ctx.identificador().getText()
        argumentos = []
        if ctx.lista_argumentos() is not None:
            es_agregacion = nombre in AGREGACIONES
            previo = self.modo_columna
            self.modo_columna = es_agregacion or previo
            try:
                argumentos = [
                    self.visit(e) for e in ctx.lista_argumentos().expresion()
                ]
            finally:
                self.modo_columna = previo
        if self.invocar is None:
            raise ErrorArepa("No hay funciones disponibles en este contexto.")
        return self.invocar(nombre, argumentos, ctx)
