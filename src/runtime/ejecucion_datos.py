"""Visitor: operaciones de datos.

Mixin sin estado independiente; EjecutorArepa aporta contexto, símbolos y
evaluador. Las operaciones siguen recorriendo el árbol ANTLR real.
"""

import os
from datos.escritor_csv import EscritorCSV
from datos.fila import Fila
from datos.lector_csv import LectorCSV
from datos.tabla import Tabla
from datos.tipos import NADA, convertir_a_tipo, es_nada, es_numero, nombre_tipo, formatear_numero as _num
from errores_base import (
    ErrorArepa,
    ErrorArchivo,
    ErrorColumna,
    ErrorEjecucion,
    ErrorSemantico,
    ErrorTipos,
    completar_ubicacion,
)
from ml.modelo import ModeloClasificacion, ModeloRegresion

class EjecucionDatos:
    def _cargar(self, ctx_monte):
        ruta = self.evaluador.evaluar(ctx_monte.cadena())
        separador = ","
        con_encabezado = True
        opciones = ctx_monte.opciones_archivo()
        if opciones is not None:
            for opcion in opciones.opcion_archivo():
                if opcion.ENCABEZADO() is not None:
                    if opcion.FALSO() is not None:
                        con_encabezado = False
                elif opcion.SEPARADOR() is not None:
                    separador = self.evaluador.evaluar(opcion.cadena())
        lector = LectorCSV(separador=separador, con_encabezado=con_encabezado)
        try:
            return lector.leer(ruta, nombre_tabla=ctx_monte.cadena().getText().strip('"'))
        except ErrorArepa as problema:
            problema.archivo_datos = ruta
            completar_ubicacion(problema, ctx_monte)
            raise

    def _aplicar_operacion(self, etapa, tabla):
        try:
            return self._aplicar_operacion_con_tabla(etapa, tabla)
        except ErrorArepa as problema:
            completar_ubicacion(problema, etapa)
            raise

    def _aplicar_operacion_con_tabla(self, etapa, tabla):
        op = etapa.operacion_datos()

        if op.JUNTE() is None and op.RESUMA() is None:
            # Un 'junte' solo prepara el 'resuma' inmediato: si otra
            # operación se interpone, las claves rezagadas se descartan.
            self._claves_junte = None

        if op.ESCOJA() is not None:
            return tabla.seleccionar(self._nombres_lista(op.lista_columnas()))

        if op.DEJE() is not None:
            condicion = op.expresion_logica()
            return tabla.filtrar(
                lambda f: self.evaluador.evaluar(condicion, f, tabla) is True
            )

        if op.ACOMODE() is not None:
            claves = [(n, "pa_arriba") for n in self._nombres_lista(op.lista_columnas())]
            direccion = op.direccion()
            if direccion is not None:
                # La gramática solo admite pa_arriba/pa_abajo, así que el
                # texto siempre es una dirección válida.
                claves = [(n, direccion.getText()) for n, _ in claves]
            return tabla.ordenar(claves)

        if op.CREE() is not None:
            nombre = op.nombre_columna(0).getText()
            expresion = op.expresion_logica()
            copia = tabla.copiar()
            copia.crear_columna(
                nombre, lambda f: self.evaluador.evaluar(expresion, f, tabla)
            )
            return copia

        if op.RENOMBRE() is not None:
            copia = tabla.copiar()
            copia.renombrar(
                op.nombre_columna(0).getText(), op.nombre_columna(1).getText()
            )
            return copia

        if op.LIMPIE() is not None:
            copia = tabla.copiar()
            if op.DUPLICADOS() is not None:
                if op.expresion_logica() is not None:
                    raise ErrorSemantico(
                        "'limpie duplicados' no recibe valor con 'con': "
                        "usá 'limpie duplicados' solo o 'limpie vacios con VALOR'.",
                        linea=op.start.line,
                        columna=op.start.column,
                    )
                copia.quitar_duplicados()
                return copia
            relleno = op.expresion_logica()
            if relleno is not None:
                copia.rellenar_vacios(self.evaluador.evaluar(relleno))
            else:
                copia.eliminar_filas_con_vacios()
            return copia

        if op.CONVIERTA() is not None:
            copia = tabla.copiar()
            tipo_destino = op.tipo_dato().getText()
            copia.convertir_columna(
                op.nombre_columna(0).getText(),
                tipo_destino,
                lambda v, contexto: convertir_a_tipo(v, tipo_destino, contexto),
            )
            return copia

        if op.JUNTE() is not None:
            self._claves_junte = self._nombres_lista(op.lista_columnas())
            return tabla

        if op.RESUMA() is not None:
            return self._ejecutar_resuma(op, tabla)

        if op.PREDIGA() is not None:
            modelo = self._obtener_modelo(op.identificador().getText(), op)
            if not isinstance(modelo, ModeloRegresion):
                raise ErrorSemantico(
                    "'prediga' necesita un modelo de regresión (creado con "
                    "'regresion'); para etiquetas usá 'clasifique'.",
                    linea=op.start.line,
                    columna=op.start.column,
                )
            return self._agregar_prediccion(
                tabla, modelo, op.nombre_columna(0).getText(), op
            )

        if op.CLASIFIQUE() is not None:
            modelo = self._obtener_modelo(op.identificador().getText(), op)
            if not isinstance(modelo, ModeloClasificacion):
                raise ErrorSemantico(
                    "'clasifique' necesita un modelo de clasificación "
                    "(perceptron o arbol); para números usá 'prediga'.",
                    linea=op.start.line,
                    columna=op.start.column,
                )
            return self._agregar_prediccion(
                tabla, modelo, op.nombre_columna(0).getText(), op
            )

        raise ErrorEjecucion("Operacion de datos no reconocida.")

    def _agregar_prediccion(self, tabla, modelo, nombre_columna, ctx):
        """Agrega al pipeline una columna con la predicción fila por fila."""
        if tabla.tiene_columna(nombre_columna):
            raise ErrorColumna(
                "La columna '{0}' ya existe en '{1}'; escogé otro nombre para "
                "la predicción.".format(nombre_columna, tabla.nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        copia = tabla.copiar()
        copia.crear_columna(
            nombre_columna, lambda fila: modelo.predecir_fila(fila, tabla)
        )
        return copia

    @staticmethod
    def _nombres_lista(ctx_lista):
        return [n.getText() for n in ctx_lista.nombre_columna()]

    def _ejecutar_resuma(self, op, tabla):
        claves = self._claves_junte or []
        self._claves_junte = None

        alias = []
        llamadas = []
        for item in op.item_resumen():
            alias.append(item.nombre_columna().getText())
            llamadas.append(item.llamada_funcion())

        grupos = tabla.agrupar(claves) if claves else [((), tabla.filas)]

        nombres_resultado = list(claves) + alias
        filas_resultado = []
        for clave, filas_grupo in grupos:
            self._grupo_filas = filas_grupo
            self._tabla_grupo = tabla
            self._en_resuma = True
            self.evaluador.modo_resuma = True
            try:
                valores = list(clave)
                for llamada in llamadas:
                    valores.append(self.evaluador.evaluar(llamada))
                filas_resultado.append(Fila(valores))
            finally:
                self._en_resuma = False
                self.evaluador.modo_resuma = False
                self._grupo_filas = None
                self._tabla_grupo = None

        return Tabla(nombres_resultado, filas_resultado, tabla.nombre, tabla.origen)

    def _calcular_agregacion(self, nombre, argumentos, ctx):
        """Calcula una agregacion propia sobre las filas del grupo actual."""
        if nombre == "cuente" and not argumentos:
            return len(self._grupo_filas)

        if not argumentos:
            raise ErrorSemantico(
                "La agregacion '{0}' necesita el nombre de una columna: "
                "{0}(columna).".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        columna = argumentos[0]
        indice = self._tabla_grupo.indice_columna(columna)
        valores = [f.valor_en(indice) for f in self._grupo_filas]
        return self._calcular_sobre_valores(
            nombre, valores, "la columna '{0}'".format(columna)
        )

    def _calcular_sobre_valores(self, nombre, valores, descripcion):
        """Aplica una agregacion a valores ya reunidos (ignora los 'nada')."""
        presentes = [v for v in valores if not es_nada(v)]

        if nombre == "cuente":
            return len(presentes)
        if nombre == "sume":
            self._exigir_numericos(presentes, nombre, descripcion)
            return sum(presentes) if presentes else NADA
        if nombre == "promedie":
            self._exigir_numericos(presentes, nombre, descripcion)
            return sum(presentes) / len(presentes) if presentes else NADA
        if nombre == "mediana":
            self._exigir_numericos(presentes, nombre, descripcion)
            return self._mediana(presentes)
        if nombre == "minimo":
            return self._extremo(presentes, nombre, descripcion, menor=True)
        if nombre == "maximo":
            return self._extremo(presentes, nombre, descripcion, menor=False)
        if nombre == "desviacion":
            self._exigir_numericos(presentes, nombre, descripcion)
            return self._desviacion(presentes)
        raise ErrorSemantico("Agregacion '{0}' no reconocida.".format(nombre))

    @staticmethod
    def _exigir_numericos(valores, agregacion, descripcion):
        for v in valores:
            if not es_numero(v):
                raise ErrorTipos(
                    "La agregacion '{0}' necesita numeros, pero {1} contiene "
                    "un valor de tipo {2}.".format(
                        agregacion, descripcion, nombre_tipo(v)
                    )
                )

    def _mediana(self, valores):
        """Mediana con orden por insercion propio (sin sorted())."""
        if not valores:
            return NADA
        ordenados = self._ordenar_insercion(valores)
        n = len(ordenados)
        medio = n // 2
        if n % 2 == 1:
            return ordenados[medio]
        return (ordenados[medio - 1] + ordenados[medio]) / 2

    @staticmethod
    def _ordenar_insercion(valores):
        ordenados = list(valores)
        for i in range(1, len(ordenados)):
            actual = ordenados[i]
            j = i - 1
            while j >= 0 and ordenados[j] > actual:
                ordenados[j + 1] = ordenados[j]
                j -= 1
            ordenados[j + 1] = actual
        return ordenados

    @staticmethod
    def _extremo(valores, agregacion, descripcion, menor):
        if not valores:
            return NADA
        EjecucionDatos._exigir_numericos(valores, agregacion, descripcion)
        extremo = valores[0]
        for v in valores[1:]:
            if (v < extremo) if menor else (v > extremo):
                extremo = v
        return extremo

    @staticmethod
    def _desviacion(valores):
        """Desviacion estandar poblacional propia: raiz de la varianza."""
        n = len(valores)
        if n < 2:
            return NADA
        promedio = sum(valores) / n
        if isinstance(promedio, float) and promedio != promedio:
            return NADA
        varianza = sum((v - promedio) ** 2 for v in valores) / n
        resultado = varianza ** 0.5
        if isinstance(resultado, float) and resultado != resultado:
            return NADA
        return resultado

    def visitInstruccion_guarde(self, ctx):
        nombre = ctx.identificador().getText()
        ruta = self.evaluador.evaluar(ctx.cadena())
        tabla = self._obtener_tabla(nombre, ctx)
        try:
            EscritorCSV().escribir(ruta, tabla)
        except (OSError, UnicodeError, ValueError) as problema:
            error = ErrorArchivo(
                "No pude guardar el CSV en '{0}': {1}.".format(ruta, problema),
                linea=ctx.start.line, columna=ctx.start.column)
            error.archivo_datos = ruta
            raise error from None
        self.contexto.registrar_archivo(ruta, "csv", os.path.getsize(ruta))
        self.contexto.imprimir(
            "[guarde] La tabla '{0}' quedo escrita en '{1}' ({2} filas).".format(
                nombre, ruta, tabla.num_filas
            )
        )

    def visitInstruccion_describa(self, ctx):
        nombre = ctx.identificador().getText()
        tabla = self._obtener_tabla(nombre, ctx)
        self.contexto.imprimir(self._resumen_texto(tabla))

    def _resumen_texto(self, tabla):
        """Resumen estadistico propio (reemplaza a pandas describe())."""
        lineas = [
            "Resumen de '{0}': {1} filas, {2} columnas".format(
                tabla.nombre, tabla.num_filas, len(tabla.columnas)
            )
        ]
        for i, columna in enumerate(tabla.columnas):
            valores = [
                f.valor_en(i) for f in tabla.filas if not es_nada(f.valor_en(i))
            ]
            partes = ["{0} ({1}): {2} valores".format(
                columna.nombre, columna.tipo, len(valores)
            )]
            if columna.tipo == "numero" and valores:
                partes.append("sume={0}".format(_num(sum(valores))))
                partes.append("promedie={0}".format(_num(sum(valores) / len(valores))))
                partes.append("mediana={0}".format(_num(self._mediana(valores))))
                partes.append("minimo={0}".format(_num(min(valores))))
                partes.append("maximo={0}".format(_num(max(valores))))
                partes.append("desviacion={0}".format(_num(self._desviacion(valores))))
            lineas.append("  " + ", ".join(partes))
        return "\n".join(lineas)
