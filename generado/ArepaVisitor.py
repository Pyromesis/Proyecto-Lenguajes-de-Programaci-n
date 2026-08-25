# Generated from gramatica/Arepa.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ArepaParser import ArepaParser
else:
    from ArepaParser import ArepaParser

# This class defines a complete generic visitor for a parse tree produced by ArepaParser.

class ArepaVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ArepaParser#programa.
    def visitPrograma(self, ctx:ArepaParser.ProgramaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#sentencias.
    def visitSentencias(self, ctx:ArepaParser.SentenciasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#sentencia.
    def visitSentencia(self, ctx:ArepaParser.SentenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_llamada.
    def visitInstruccion_llamada(self, ctx:ArepaParser.Instruccion_llamadaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#asignacion.
    def visitAsignacion(self, ctx:ArepaParser.AsignacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_guarde.
    def visitInstruccion_guarde(self, ctx:ArepaParser.Instruccion_guardeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_devolver.
    def visitInstruccion_devolver(self, ctx:ArepaParser.Instruccion_devolverContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_cuenteme.
    def visitInstruccion_cuenteme(self, ctx:ArepaParser.Instruccion_cuentemeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_describa.
    def visitInstruccion_describa(self, ctx:ArepaParser.Instruccion_describaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#definicion_funcion.
    def visitDefinicion_funcion(self, ctx:ArepaParser.Definicion_funcionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#parametros.
    def visitParametros(self, ctx:ArepaParser.ParametrosContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#condicional.
    def visitCondicional(self, ctx:ArepaParser.CondicionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#bloque.
    def visitBloque(self, ctx:ArepaParser.BloqueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#expresion.
    def visitExpresion(self, ctx:ArepaParser.ExpresionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#etapa_pipeline.
    def visitEtapa_pipeline(self, ctx:ArepaParser.Etapa_pipelineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#operacion_datos.
    def visitOperacion_datos(self, ctx:ArepaParser.Operacion_datosContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_monte.
    def visitInstruccion_monte(self, ctx:ArepaParser.Instruccion_monteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#opciones_archivo.
    def visitOpciones_archivo(self, ctx:ArepaParser.Opciones_archivoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#opcion_archivo.
    def visitOpcion_archivo(self, ctx:ArepaParser.Opcion_archivoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#direccion.
    def visitDireccion(self, ctx:ArepaParser.DireccionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#lista_columnas.
    def visitLista_columnas(self, ctx:ArepaParser.Lista_columnasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#item_resumen.
    def visitItem_resumen(self, ctx:ArepaParser.Item_resumenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#tipo_dato.
    def visitTipo_dato(self, ctx:ArepaParser.Tipo_datoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#instruccion_grafica.
    def visitInstruccion_grafica(self, ctx:ArepaParser.Instruccion_graficaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#tipo_grafica.
    def visitTipo_grafica(self, ctx:ArepaParser.Tipo_graficaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#clausula_estetica.
    def visitClausula_estetica(self, ctx:ArepaParser.Clausula_esteticaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#final_grafica.
    def visitFinal_grafica(self, ctx:ArepaParser.Final_graficaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#expresion_logica.
    def visitExpresion_logica(self, ctx:ArepaParser.Expresion_logicaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#conjuncion.
    def visitConjuncion(self, ctx:ArepaParser.ConjuncionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#negacion.
    def visitNegacion(self, ctx:ArepaParser.NegacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#comparacion.
    def visitComparacion(self, ctx:ArepaParser.ComparacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#operador_relacional.
    def visitOperador_relacional(self, ctx:ArepaParser.Operador_relacionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#aritmetica.
    def visitAritmetica(self, ctx:ArepaParser.AritmeticaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#termino.
    def visitTermino(self, ctx:ArepaParser.TerminoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#factor.
    def visitFactor(self, ctx:ArepaParser.FactorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#unario.
    def visitUnario(self, ctx:ArepaParser.UnarioContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#atomo.
    def visitAtomo(self, ctx:ArepaParser.AtomoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#llamada_funcion.
    def visitLlamada_funcion(self, ctx:ArepaParser.Llamada_funcionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#lista_argumentos.
    def visitLista_argumentos(self, ctx:ArepaParser.Lista_argumentosContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#cadena.
    def visitCadena(self, ctx:ArepaParser.CadenaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#identificador.
    def visitIdentificador(self, ctx:ArepaParser.IdentificadorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArepaParser#nombre_columna.
    def visitNombre_columna(self, ctx:ArepaParser.Nombre_columnaContext):
        return self.visitChildren(ctx)



del ArepaParser