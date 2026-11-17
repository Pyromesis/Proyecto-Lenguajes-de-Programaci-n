"""Punto de entrada del Visitor de AREPA.

Coordina estado, símbolos y expresiones. Los visitantes de datos, gráficas,
control, estructuras y modelos viven en módulos separados y comparten el
mismo contexto de ejecución, sin duplicar el motor ni usar eval/exec.
"""

from ArepaVisitor import ArepaVisitor
from datos import acceso
from datos.tabla import Tabla
from datos.tipos import nombre_tipo
from errores_base import (
    ErrorArepa,
    ErrorEjecucion,
    ErrorSemantico,
    ErrorTipos,
    ErrorVariable,
    RetornoFuncion,
    SalirCiclo,
    SeguirCiclo,
    completar_ubicacion,
)
from expresiones.evaluador import EvaluadorExpresiones
from runtime.contexto import ContextoEjecucion
from runtime.simbolos import FuncionArepa
from runtime.ejecucion_datos import EjecucionDatos
from runtime.ejecucion_graficas import EjecucionGraficas
from runtime.ejecucion_control import EjecucionControl
from runtime.ejecucion_estructuras import EjecucionEstructuras
from runtime.ejecucion_modelos import EjecucionModelos

AGREGACIONES = ("cuente", "sume", "promedie", "mediana", "minimo", "maximo", "desviacion")
MAX_VUELTAS_CICLO = 1000000


class EjecutorArepa(
    EjecucionDatos, EjecucionGraficas, EjecucionControl,
    EjecucionEstructuras, EjecucionModelos, ArepaVisitor,
):
    """Interpreta un programa completo mediante visitantes por responsabilidad."""

    @property
    def limite_vueltas(self):
        """Límite compartido y configurable para pruebas de ciclos."""
        return MAX_VUELTAS_CICLO

    def __init__(self):
        self.contexto = ContextoEjecucion()
        self.evaluador = EvaluadorExpresiones(
            self.contexto.simbolos,
            invocar=self._invocar,
            evaluar_expresion=self.evaluar_expresion,
            advertir=self.contexto.advertir,
        )
        self._ambito = self.contexto.simbolos
        self._claves_junte = None
        self._en_resuma = False
        self._grupo_filas = None
        self._tabla_grupo = None
        self._ultima_ubicacion = (-1, -1)

    def visit(self, ctx):
        if getattr(ctx, "start", None) is not None:
            self._ultima_ubicacion = (ctx.start.line, ctx.start.column)
        try:
            return super().visit(ctx)
        except ErrorArepa as problema:
            completar_ubicacion(problema, ctx)
            raise

    def ejecutar(self, arbol):
        """Ejecuta el programa completo a partir de la raiz del arbol."""
        try:
            self.visit(arbol)
        except RecursionError:
            raise ErrorEjecucion(
                "La recursión es muy profunda y se agotó la pila: revisá "
                "el caso base de la función o probá con un número más chico.",
                linea=self._ultima_ubicacion[0], columna=self._ultima_ubicacion[1],
            )
        except RetornoFuncion:
            raise ErrorSemantico(
                "'devuelva' solo puede usarse dentro de una función definida "
                "con 'invente'.",
                linea=self._ultima_ubicacion[0], columna=self._ultima_ubicacion[1],
            )
        except SalirCiclo as senal:
            raise ErrorSemantico(
                "'pare' solo puede usarse dentro de un ciclo 'repita' o "
                "'mientras'.",
                linea=senal.linea,
                columna=senal.columna,
            )
        except SeguirCiclo as senal:
            raise ErrorSemantico(
                "'siga' solo puede usarse dentro de un ciclo 'repita' o "
                "'mientras'.",
                linea=senal.linea,
                columna=senal.columna,
            )

    def visitPrograma(self, ctx):
        if ctx.sentencias() is not None:
            self.visit(ctx.sentencias())

    def visitSentencias(self, ctx):
        for sentencia in ctx.sentencia():
            self.visit(sentencia)

    def visitSentencia(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitAsignacion(self, ctx):
        nombre = ctx.identificador().getText()
        indices = ctx.indice()

        if indices:
            contenedor = self._ambito.buscar_opcional(nombre)
            if contenedor is None:
                raise ErrorVariable(
                    "La variable '{0}' no esta declarada; no se puede "
                    "asignar dentro de ella.".format(nombre),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            for indice in indices[:-1]:
                posicion = self.evaluar_expresion(indice.expresion())
                contenedor = acceso.obtener(
                    contenedor, posicion, indice.start.line, indice.start.column
                )
            ultimo = indices[-1]
            posicion = self.evaluar_expresion(ultimo.expresion())
            valor = self.visit(ctx.expresion())
            acceso.asignar(
                contenedor, posicion, valor,
                ultimo.start.line, ultimo.start.column,
            )
            return valor

        valor = self.visit(ctx.expresion())
        if self._ambito.existe(nombre):
            self._ambito.asignar(nombre, valor)
        else:
            self._ambito.declarar(nombre, valor)
        return valor

    def evaluar_expresion(self, ctx):
        """Callback del evaluador: una expresion puede ser un pipeline."""
        return self.visitExpresion(ctx)

    def visitExpresion(self, ctx):
        """Pipeline: primera etapa y encadenamiento con '|>'.

        La primera etapa carga (monte), referencia una variable que sea
        tabla o calcula un valor simple. Cada etapa siguiente debe ser
        una operacion sobre la tabla que llega del paso anterior.
        """
        etapas = ctx.etapa_pipeline()
        valor = self._evaluar_primera_etapa(etapas[0])
        for etapa in etapas[1:]:
            if not isinstance(valor, Tabla):
                raise ErrorSemantico(
                    "El operador '|>' necesita una tabla a su izquierda, pero "
                    "la etapa anterior produjo un valor de tipo {0}.".format(
                        nombre_tipo(valor)
                    ),
                    linea=etapa.start.line,
                    columna=etapa.start.column,
                )
            valor = self._aplicar_operacion(etapa, valor)
        return valor

    def _evaluar_primera_etapa(self, etapa):
        operacion = etapa.operacion_datos()
        if operacion is None:
            # La expresion puede venir de un callback del evaluador (por
            # ejemplo un parentesis dentro de 'deje donde'): se conserva
            # la fila/tabla actuales para resolver nombres de columna.
            fila_actual, tabla_actual = self.evaluador.tomar_contexto_fila()[:2]
            return self.evaluador.evaluar(
                etapa.expresion_logica(), fila_actual, tabla_actual
            )
        if operacion.instruccion_monte() is not None:
            return self._cargar(operacion.instruccion_monte())
        raise ErrorSemantico(
            "La etapa '{0}' necesita una tabla de entrada: encadenala con "
            "'|>' despues de una tabla o cargala con 'monte' o creala con "
            "'arme'.".format(operacion.start.text),
            linea=operacion.start.line,
            columna=operacion.start.column,
        )

    def _obtener_tabla(self, nombre, ctx):
        valor = self._ambito.buscar_opcional(nombre)
        if valor is None:
            raise ErrorVariable(
                "La variable '{0}' no esta declarada; no hay ninguna tabla "
                "para usar en esta instruccion.".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(valor, Tabla):
            raise ErrorTipos(
                "'{0}' no es una tabla (es de tipo {1}); esta instruccion "
                "solo trabaja con tablas cargadas con 'monte', creadas con "
                "'arme' o producidas por un pipeline.".format(
                    nombre, nombre_tipo(valor)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return valor

    def visitInstruccion_cuenteme(self, ctx):
        valores = []
        if ctx.lista_argumentos() is not None:
            valores = [self.visit(e) for e in ctx.lista_argumentos().expresion()]
        self.contexto.imprimir(*valores)

    def visitInstruccion_llamada(self, ctx):
        return self.visit(ctx.llamada_funcion())

    def visitLlamada_funcion(self, ctx):
        """Una llamada suelta la resuelve el evaluador de expresiones."""
        return self.evaluador.evaluar(ctx)

    def _invocar(self, nombre, argumentos, ctx):
        if nombre in AGREGACIONES:
            if self._en_resuma and self._grupo_filas is not None:
                return self._calcular_agregacion(nombre, argumentos, ctx)
            return self._agregacion_fuera_de_resuma(nombre, argumentos, ctx)

        if nombre == "largo":
            return self._largo(argumentos, ctx)
        if nombre == "columna":
            return self._columna(argumentos, ctx)
        if nombre == "columnas":
            return self._columnas(argumentos, ctx)

        funcion = self._ambito.buscar_opcional(nombre)
        if isinstance(funcion, FuncionArepa):
            return self._llamar_funcion(funcion, argumentos, ctx)

        raise ErrorSemantico(
            "La funcion '{0}' no existe. Definila con 'invente {0}(...) {{ ... }}' "
            "o usa una agregacion (sume, promedie, ...) dentro de 'resuma'.".format(nombre),
            linea=ctx.start.line,
            columna=ctx.start.column,
        )
