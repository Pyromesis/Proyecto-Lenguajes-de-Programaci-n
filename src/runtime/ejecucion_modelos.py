"""Visitor: operaciones de modelos.

Mixin sin estado independiente; EjecutorArepa aporta contexto, símbolos y
evaluador. Las operaciones siguen recorriendo el árbol ANTLR real.
"""

from datos.tipos import nombre_tipo
from errores_base import ErrorArepa, ErrorSemantico, ErrorTipos, ErrorVariable
from ml import metricas
from ml.arbol_decision import ArbolDecision
from ml.modelo import ModeloML, ModeloRegresion
from ml.perceptron import Perceptron
from ml.preprocesamiento import Preprocesador
from ml.regresion_lineal import RegresionLineal
from utiles.enteros import texto_a_entero

class EjecucionModelos:
    def visitInstruccion_entrene(self, ctx):
        nombre_modelo = ctx.identificador(0).getText()
        nombre_tabla = ctx.identificador(1).getText()
        tabla = self._obtener_tabla(nombre_tabla, ctx)
        algoritmo = ctx.algoritmo_ml().getText()

        columnas = None
        objetivo = None
        clases = None
        tasa = 0.05
        epocas = 1000
        profundidad = 6
        min_hojas = 2
        tasa_dada = epocas_dadas = False
        profundidad_dada = min_hojas_dada = False

        for opcion in ctx.opciones_ml().opcion_ml():
            if opcion.COLUMNAS() is not None:
                columnas = self._nombres_lista(opcion.lista_columnas())
            elif opcion.OBJETIVO() is not None:
                objetivo = opcion.nombre_columna().getText()
            elif opcion.CLASES() is not None:
                clases = [
                    self._valor_etiqueta(etiqueta)
                    for etiqueta in opcion.lista_etiquetas().etiqueta()
                ]
            elif opcion.TASA() is not None:
                tasa = self.evaluador.evaluar(opcion.expresion_logica())
                tasa_dada = True
            elif opcion.EPOCAS() is not None:
                epocas = self.evaluador.evaluar(opcion.expresion_logica())
                epocas_dadas = True
            elif opcion.PROFUNDIDAD() is not None:
                profundidad = self.evaluador.evaluar(opcion.expresion_logica())
                profundidad_dada = True
            elif opcion.MIN_HOJAS() is not None:
                min_hojas = self.evaluador.evaluar(opcion.expresion_logica())
                min_hojas_dada = True

        if columnas is None:
            raise ErrorSemantico(
                "'entrene' necesita 'columnas [ ... ]' con las variables de "
                "entrada del modelo.",
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if objetivo is None:
            raise ErrorSemantico(
                "'entrene' necesita 'objetivo columna' con la variable que "
                "se quiere predecir o clasificar.",
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        if algoritmo == "regresion":
            if clases is not None:
                raise ErrorSemantico(
                    "'regresion' predice números y no usa 'clases [...]'.",
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            if profundidad_dada or min_hojas_dada:
                raise ErrorSemantico(
                    "'profundidad' y 'min_hojas' son opciones de 'arbol', "
                    "no de 'regresion'.",
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
        elif algoritmo == "perceptron":
            if profundidad_dada or min_hojas_dada:
                raise ErrorSemantico(
                    "'profundidad' y 'min_hojas' son opciones de 'arbol', "
                    "no de 'perceptron'.",
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
        elif algoritmo == "arbol":
            if tasa_dada or epocas_dadas:
                raise ErrorSemantico(
                    "'tasa' y 'epocas' son opciones de 'regresion' y "
                    "'perceptron', no de 'arbol'.",
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )

        try:
            preprocesador = Preprocesador(tabla, columnas, objetivo)
            X, y = preprocesador.datos(
                tabla, estandarizar=(algoritmo != "arbol")
            )
            if algoritmo == "regresion":
                modelo = RegresionLineal(
                    preprocesador, objetivo, tasa=tasa, epocas=epocas
                )
            elif algoritmo == "perceptron":
                modelo = Perceptron(
                    preprocesador, objetivo, tasa=tasa, epocas=epocas, clases=clases
                )
            else:
                modelo = ArbolDecision(
                    preprocesador,
                    objetivo,
                    profundidad=profundidad,
                    min_hojas=min_hojas,
                    clases=clases,
                )
            modelo.nombre = nombre_modelo
            modelo.entrenar(X, y)
        except ErrorArepa as problema:
            self._con_ubicacion(problema, ctx)
            raise

        self._asignar_variable(nombre_modelo, modelo)
        self.contexto.imprimir(
            "[entrene] Modelo '{0}' ({1}) entrenado con {2} fila(s), {3} "
            "columna(s); objetivo '{4}'.".format(
                nombre_modelo,
                algoritmo,
                len(y),
                len(columnas),
                objetivo,
            )
        )
        return modelo

    def visitInstruccion_evalua(self, ctx):
        nombre_modelo = ctx.identificador(0).getText()
        nombre_tabla = ctx.identificador(1).getText()
        modelo = self._obtener_modelo(nombre_modelo, ctx)
        tabla = self._obtener_tabla(nombre_tabla, ctx)
        try:
            reales, predicciones = modelo.evaluar(tabla)
        except ErrorArepa as problema:
            self._con_ubicacion(problema, ctx)
            raise

        if isinstance(modelo, ModeloRegresion):
            texto = metricas.resumen_regresion(reales, predicciones)
        else:
            texto = metricas.resumen_clasificacion(
                reales, predicciones, getattr(modelo, "clases", None)
            )
        self.contexto.imprimir(
            "[evalua] Modelo '{0}' sobre '{1}':\n{2}".format(
                nombre_modelo, nombre_tabla, texto
            )
        )

    def _obtener_modelo(self, nombre, ctx):
        valor = self._ambito.buscar_opcional(nombre)
        if valor is None:
            raise ErrorVariable(
                "El modelo '{0}' no está declarado; entrenalo primero con "
                "'entrene {0} = ...'.".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(valor, ModeloML):
            raise ErrorTipos(
                "'{0}' no es un modelo de machine learning (es de tipo "
                "{1}).".format(nombre, nombre_tipo(valor)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return valor

    def _valor_etiqueta(self, ctx):
        """Valor de una etiqueta de 'clases [ ... ]'."""
        if ctx.cadena() is not None:
            return self.evaluador.evaluar(ctx.cadena())
        if ctx.ENTERO() is not None:
            return texto_a_entero(ctx.getText())
        if ctx.DECIMAL() is not None:
            return float(ctx.getText())
        if ctx.OBVIO() is not None:
            return True
        return False

    @staticmethod
    def _con_ubicacion(problema, ctx):
        if getattr(problema, "linea", -1) == -1:
            problema.linea = ctx.start.line
            problema.columna = ctx.start.column
        return problema
