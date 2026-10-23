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

Modos especiales:
  * 'modo_columna': durante las agregaciones de 'resuma' los argumentos
    son nombres de columnas, no valores; con esta bandera el nombre se
    devuelve tal cual;
  * 'modo_resuma': lo activa el ejecutor solo mientras evalúa los items
    de 'resuma'. Las agregaciones usadas fuera de 'resuma' evalúan su
    primer argumento como valor (tabla o lista) y los siguientes como
    nombres de columna o textos.

Las expresiones generales (pipelines, listas, registros, tablas y
argumentos) se delegan al ejecutor mediante el callback
'evaluar_expresion'; así 'cuenteme t |> escoja [a]' y los literales
pueden contener pipelines completos.

Limitaciones:
  * la ubicacion (linea/columna) de un error de tipos es aproximada:
    se reporta la posicion donde inicia la expresion.
"""

import re

from datos import acceso
from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import NADA
from errores_base import ErrorArepa, ErrorSemantico, ErrorTipos, ErrorVariable
from expresiones import operadores as ops

from ArepaVisitor import ArepaVisitor

# Un identificador simple del DSL (letras/underscore y luego letras,
# digitos y underscore). Se usa para aceptar nombres de columna sin
# confundirlos con variables.
_PATRON_IDENTIFICADOR = re.compile(r"^[^\W\d]\w*$")

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

# Agregaciones del lenguaje: dentro de 'resuma' sus argumentos son
# NOMBRES de columnas; fuera de 'resuma' reciben una tabla + columna o
# una lista.
AGREGACIONES = (
    "cuente", "sume", "promedie", "mediana", "minimo", "maximo", "desviacion",
)

# Funciones que, además del valor, reciben un nombre de columna simple.
FUNCIONES_CON_NOMBRE_DE_COLUMNA = ("columna",)


class EvaluadorExpresiones(ArepaVisitor):
    """Calcula el valor de las expresiones del DSL sobre su arbol."""

    def __init__(self, simbolos, invocar=None, evaluar_expresion=None):
        super().__init__()
        self.simbolos = simbolos
        self.invocar = invocar
        self.evaluar_expresion = evaluar_expresion
        self._fila = None
        self._tabla = None
        self.modo_columna = False
        self.modo_resuma = False

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

    def tomar_contexto_fila(self):
        """Guarda (fila, tabla, modo_columna, modo_resuma) para llamadas."""
        return (self._fila, self._tabla, self.modo_columna, self.modo_resuma)

    def fijar_contexto_fila(self, fila, tabla, modo_columna=False, modo_resuma=False):
        """Restaura el contexto de fila (lo usa el ejecutor al llamar)."""
        self._fila, self._tabla = fila, tabla
        self.modo_columna, self.modo_resuma = modo_columna, modo_resuma

    # ---------------------------------------------------------------- #
    # Expresiones generales: las resuelve el ejecutor (pipeline)
    # ---------------------------------------------------------------- #

    def visitExpresion(self, ctx):
        """Delega una expresion completa al ejecutor (etapas de pipeline)."""
        if self.evaluar_expresion is None:
            raise ErrorArepa(
                "Error interno: el evaluador necesita el callback "
                "'evaluar_expresion' para evaluar una expresion completa."
            )
        return self.evaluar_expresion(ctx)

    def _evaluar_expresion(self, ctx):
        """Evalua un nodo 'expresion' usando el callback del ejecutor."""
        return self.visitExpresion(ctx)

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
        valor = self.visit(ctx.unario(0))
        for i in range(1, len(ctx.unario())):
            operador = ctx.getChild(2 * i - 1).getText()
            valor = OPERADORES_ARITMETICOS[operador](valor, self.visit(ctx.unario(i)))
        return valor

    def visitUnario(self, ctx):
        if ctx.MENOS() is not None:
            return ops.negar_numero(self.visit(ctx.unario()))
        return self.visit(ctx.potencia())

    def visitPotencia(self, ctx):
        base = self.visit(ctx.acceso())
        if ctx.POTENCIA() is not None:
            return ops.potenciar(base, self.visit(ctx.unario()))
        return base

    def visitAcceso(self, ctx):
        valor = self.visit(ctx.atomo())
        for indice in ctx.indice():
            posicion = self._evaluar_expresion(indice.expresion())
            valor = acceso.obtener(
                valor, posicion, indice.start.line, indice.start.column
            )
        return valor

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
        if ctx.lista_literal() is not None:
            return self.visit(ctx.lista_literal())
        if ctx.registro_literal() is not None:
            return self.visit(ctx.registro_literal())
        if ctx.tabla_literal() is not None:
            return self.visit(ctx.tabla_literal())
        if ctx.llamada_funcion() is not None:
            return self.visit(ctx.llamada_funcion())
        if ctx.nombre_columna() is not None:
            return self._resolver_nombre(ctx.nombre_columna())
        return self._evaluar_expresion(ctx.expresion())

    # ---------------------------------------------------------------- #
    # Literales de Lista, Registro y Tabla
    # ---------------------------------------------------------------- #

    def visitLista_literal(self, ctx):
        return Lista(self._evaluar_expresion(e) for e in ctx.expresion())

    def visitRegistro_literal(self, ctx):
        pares = []
        for par in ctx.par_registro():
            clave_ctx = par.clave_registro()
            if clave_ctx.cadena() is not None:
                clave = self.visit(clave_ctx.cadena())
            else:
                clave = clave_ctx.nombre_columna().getText()
            pares.append((clave, self._evaluar_expresion(par.expresion())))
        return Registro(pares)

    def visitTabla_literal(self, ctx):
        nombres = [c.getText() for c in ctx.lista_columnas().nombre_columna()]
        filas = []
        for fila_ctx in ctx.fila_literal():
            valores = [self._evaluar_expresion(e) for e in fila_ctx.expresion()]
            if len(valores) != len(nombres):
                raise ErrorTipos(
                    "La fila {0} de 'arme' trae {1} {2} pero se declararon "
                    "{3} columnas: {4}.".format(
                        len(filas) + 1,
                        len(valores),
                        "valor" if len(valores) == 1 else "valores",
                        len(nombres),
                        ", ".join(nombres),
                    ),
                    linea=fila_ctx.start.line,
                    columna=fila_ctx.start.column,
                )
            filas.append(valores)
        return Tabla.desde_filas(nombres, filas, nombre="tabla", origen="arme")

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
                indice = self._tabla.indice_columna(nombre)
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
            expresiones = ctx.lista_argumentos().expresion()
            if nombre in AGREGACIONES and self.modo_resuma:
                # Dentro de 'resuma' todos los argumentos son columnas.
                previo = self.modo_columna
                self.modo_columna = True
                try:
                    argumentos = [self.visit(e) for e in expresiones]
                finally:
                    self.modo_columna = previo
            elif nombre in AGREGACIONES:
                argumentos = self._argumentos_de_agregacion(nombre, expresiones)
            elif nombre in FUNCIONES_CON_NOMBRE_DE_COLUMNA:
                argumentos = [self._evaluar_expresion(expresiones[0])]
                argumentos += [
                    self._nombre_o_valor(e) for e in expresiones[1:]
                ]
            else:
                argumentos = [self._evaluar_expresion(e) for e in expresiones]
        if self.invocar is None:
            raise ErrorArepa("No hay funciones disponibles en este contexto.")
        return self.invocar(nombre, argumentos, ctx)

    def _argumentos_de_agregacion(self, nombre, expresiones):
        """Argumentos de una agregacion fuera de 'resuma'.

        El primero se evalua normalmente (tabla o lista); los demas se
        toman como nombre de columna simple o cadena, sin resolverlos
        como variables.
        """
        try:
            primero = self._evaluar_expresion(expresiones[0])
        except ErrorVariable:
            if not _PATRON_IDENTIFICADOR.match(expresiones[0].getText()):
                raise
            raise ErrorSemantico(
                "La agregacion '{0}' necesita una tabla o una lista como "
                "primer argumento, y '{1}' no es una variable. Recordá que "
                "'{0}(columna)' solo puede usarse dentro de 'resuma'; fuera "
                "de 'resuma' usá '{0}(tabla, columna)' o '{0}(lista)'.".format(
                    nombre, expresiones[0].getText()
                ),
                linea=expresiones[0].start.line,
                columna=expresiones[0].start.column,
            )
        return [primero] + [
            self._nombre_o_valor(e) for e in expresiones[1:]
        ]

    def _nombre_o_valor(self, ctx):
        """Texto de un identificador simple o una cadena; si no, su valor."""
        texto = ctx.getText()
        if len(texto) >= 2 and texto.startswith('"') and texto.endswith('"'):
            return self._desescapar(texto[1:-1])
        if _PATRON_IDENTIFICADOR.match(texto):
            return texto
        return self._evaluar_expresion(ctx)
