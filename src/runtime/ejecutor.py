"""
AREPA - Ejecutor propio del DSL (src/runtime/ejecutor.py)
---------------------------------------------------------
Implementado por el equipo. Recorre el arbol de analisis generado por
ANTLR4 (uso autorizado) y ejecuta el programa: sentencias, pipeline de
datos, funciones, condicionales y agregaciones.

Toda la logica es propia:
  * el pipeline aplica las operaciones de datos/tabla.py sobre la Tabla
    propia, una etapa a la vez (decision D3: cada etapa produce una
    tabla nueva sin modificar la anterior);
  * 'junte por [...] |> resuma ...' agrupa con Tabla.agrupar y calcula
    las agregaciones (cuente, sume, promedie, mediana, minimo, maximo,
    desviacion) con algoritmos propios: la mediana usa un orden por
    insercion propio y la desviacion es la estandar poblacional;
  * las funciones 'invente' se guardan como closures propias: capturan
    el ambito donde fueron definidas y admiten recursion;
  * 'pinte' se reconoce y valida semanticamente (tabla y columnas de
    ejex/ejey), pero NO genera imagenes: eso llega en la Fase 3.

Decisiones semanticas propias (documentadas):
  * 'deje donde' conserva la fila solo si la condicion es exactamente
    obvio (True); 'nada' y 'falso' descartan la fila;
  * la condicion de 'fijese_si' debe ser logica: 'nada' es un error;
  * 'limpie vacios' sin 'con' elimina las filas con algun 'nada';
  * 'junte' prepara las claves de agrupacion para el 'resuma' siguiente;
  * 'resuma' sin 'junte' previo resume toda la tabla en una sola fila;
  * 'devuelva' fuera de una funcion es un error semantico.
"""

from datos.escritor_csv import EscritorCSV
from datos.fila import Fila
from datos.lector_csv import LectorCSV
from datos.tabla import Tabla
from datos.tipos import (
    NADA,
    convertir_a_tipo,
    es_nada,
    es_numero,
    nombre_tipo,
)
from errores_base import (
    ErrorColumna,
    ErrorEjecucion,
    ErrorSemantico,
    ErrorTipos,
    ErrorVariable,
    RetornoFuncion,
)
from expresiones.evaluador import EvaluadorExpresiones
from runtime.contexto import ContextoEjecucion, a_texto
from runtime.simbolos import FuncionArepa

from ArepaVisitor import ArepaVisitor

AGREGACIONES = (
    "cuente", "sume", "promedie", "mediana", "minimo", "maximo", "desviacion",
)

DIRECCIONES = ("pa_arriba", "pa_abajo")


class EjecutorArepa(ArepaVisitor):
    """Interpreta el arbol de analisis y produce la ejecucion del programa."""

    def __init__(self):
        self.contexto = ContextoEjecucion()
        self.evaluador = EvaluadorExpresiones(
            self.contexto.simbolos, invocar=self._invocar
        )
        self._ambito = self.contexto.simbolos
        self._claves_junte = None
        self._en_resuma = False
        self._grupo_filas = None
        self._tabla_grupo = None

    # ---------------------------------------------------------------- #
    # Entrada
    # ---------------------------------------------------------------- #

    def ejecutar(self, arbol):
        """Ejecuta el programa completo a partir de la raiz del arbol."""
        try:
            self.visit(arbol)
        except RetornoFuncion:
            raise ErrorSemantico(
                "'devuelva' solo puede usarse dentro de una función definida "
                "con 'invente'."
            )

    # ---------------------------------------------------------------- #
    # Programa y sentencias
    # ---------------------------------------------------------------- #

    def visitPrograma(self, ctx):
        if ctx.sentencias() is not None:
            self.visit(ctx.sentencias())

    def visitSentencias(self, ctx):
        for sentencia in ctx.sentencia():
            self.visit(sentencia)

    def visitSentencia(self, ctx):
        return self.visit(ctx.getChild(0))

    # ---------------------------------------------------------------- #
    # Asignaciones y pipeline
    # ---------------------------------------------------------------- #

    def visitAsignacion(self, ctx):
        nombre = ctx.identificador().getText()
        valor = self.visit(ctx.expresion())
        if self._ambito.existe(nombre):
            self._ambito.asignar(nombre, valor)
        else:
            self._ambito.declarar(nombre, valor)
        return valor

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
            return self.evaluador.evaluar(etapa.expresion_logica())
        if operacion.instruccion_monte() is not None:
            return self._cargar(operacion.instruccion_monte())
        raise ErrorSemantico(
            "La etapa '{0}' necesita una tabla de entrada: encadenala con "
            "'|>' despues de una tabla o cargala con 'monte'.".format(
                operacion.start.text
            ),
            linea=operacion.start.line,
            columna=operacion.start.column,
        )

    # ---------------------------------------------------------------- #
    # Carga de CSV ('monte')
    # ---------------------------------------------------------------- #

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
        return lector.leer(ruta, nombre_tabla=ctx_monte.cadena().getText().strip('"'))

    # ---------------------------------------------------------------- #
    # Operaciones del pipeline
    # ---------------------------------------------------------------- #

    def _aplicar_operacion(self, etapa, tabla):
        op = etapa.operacion_datos()

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
                texto = direccion.getText()
                if texto not in DIRECCIONES:
                    raise ErrorSemantico(
                        "'{0}' no es una direccion valida; usa pa_arriba o pa_abajo.".format(texto)
                    )
                claves = [(n, texto) for n, _ in claves]
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

        raise ErrorEjecucion("Operacion de datos no reconocida.")

    @staticmethod
    def _nombres_lista(ctx_lista):
        return [n.getText() for n in ctx_lista.nombre_columna()]

    # ---------------------------------------------------------------- #
    # Agrupamiento y agregaciones propias
    # ---------------------------------------------------------------- #

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
            try:
                valores = list(clave)
                for llamada in llamadas:
                    valores.append(self.evaluador.evaluar(llamada))
                filas_resultado.append(Fila(valores))
            finally:
                self._en_resuma = False
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
        valores = [
            f.valor_en(indice)
            for f in self._grupo_filas
            if not es_nada(f.valor_en(indice))
        ]

        if nombre == "cuente":
            return len(valores)
        if nombre == "sume":
            self._exigir_numericos(valores, nombre, columna)
            return sum(valores) if valores else NADA
        if nombre == "promedie":
            self._exigir_numericos(valores, nombre, columna)
            return sum(valores) / len(valores) if valores else NADA
        if nombre == "mediana":
            self._exigir_numericos(valores, nombre, columna)
            return self._mediana(valores)
        if nombre == "minimo":
            return self._extremo(valores, nombre, columna, menor=True)
        if nombre == "maximo":
            return self._extremo(valores, nombre, columna, menor=False)
        if nombre == "desviacion":
            self._exigir_numericos(valores, nombre, columna)
            return self._desviacion(valores)
        raise ErrorSemantico("Agregacion '{0}' no reconocida.".format(nombre))

    @staticmethod
    def _exigir_numericos(valores, agregacion, columna):
        for v in valores:
            if not es_numero(v):
                raise ErrorTipos(
                    "La agregacion '{0}' necesita numeros, pero la columna "
                    "'{1}' contiene un valor de tipo {2}.".format(
                        agregacion, columna, nombre_tipo(v)
                    )
                )

    def _mediana(self, valores):
        """Mediana con orden por insercion propio (sin sorted())."""
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
    def _extremo(valores, agregacion, columna, menor):
        if not valores:
            return NADA
        EjecutorArepa._exigir_numericos(valores, agregacion, columna)
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
        varianza = sum((v - promedio) ** 2 for v in valores) / n
        return varianza ** 0.5

    # ---------------------------------------------------------------- #
    # Guardar y graficar (reconocimiento con validacion semantica)
    # ---------------------------------------------------------------- #

    def visitInstruccion_guarde(self, ctx):
        nombre = ctx.identificador().getText()
        ruta = self.evaluador.evaluar(ctx.cadena())
        tabla = self._obtener_tabla(nombre, ctx)
        EscritorCSV().escribir(ruta, tabla)
        self.contexto.imprimir(
            "[guarde] La tabla '{0}' quedo escrita en '{1}' ({2} filas).".format(
                nombre, ruta, tabla.num_filas
            )
        )

    def visitInstruccion_grafica(self, ctx):
        """Fase 1: valida la instruccion y avisa que la imagen llega en Fase 3."""
        nombre = ctx.identificador().getText()
        tipo = ctx.tipo_grafica().getText()
        tabla = self._obtener_tabla(nombre, ctx)
        for clausula in ctx.clausula_estetica():
            if clausula.EJEX() is not None or clausula.EJEY() is not None:
                columna = clausula.nombre_columna().getText()
                if not tabla.tiene_columna(columna):
                    raise ErrorColumna(
                        "La grafica usa la columna '{0}' que no existe en "
                        "'{1}'. Columnas: {2}.".format(
                            columna, nombre, ", ".join(tabla.nombres_columnas)
                        ),
                        linea=clausula.start.line,
                        columna=clausula.start.column,
                    )
        self.contexto.imprimir(
            "[pinte] Grafica de {0} sobre '{1}' validada; la generacion de "
            "imagenes llega en la Fase 3.".format(tipo, nombre)
        )

    def _obtener_tabla(self, nombre, ctx):
        valor = self._ambito.buscar_opcional(nombre)
        if valor is None:
            raise ErrorVariable(
                "La variable '{0}' no esta declarada; no hay nada que "
                "exportar o graficar.".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(valor, Tabla):
            raise ErrorTipos(
                "'{0}' no es una tabla (es de tipo {1}); esta instruccion "
                "solo trabaja con tablas cargadas con 'monte'.".format(
                    nombre, nombre_tipo(valor)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return valor

    # ---------------------------------------------------------------- #
    # Condicionales, funciones y salida
    # ---------------------------------------------------------------- #

    def visitCondicional(self, ctx):
        condicion = self.evaluador.evaluar(ctx.expresion_logica())
        bloques = ctx.bloque()
        if not isinstance(bloques, list):
            bloques = [bloques]

        if condicion is True:
            self._ejecutar_bloque(bloques[0])
            return None
        if condicion is not False:
            raise ErrorTipos(
                "La condicion de 'fijese_si' debe ser obvio o falso, pero fue "
                "{0}.".format(a_texto(condicion)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        if ctx.SINO() is not None:
            alterno = ctx.condicional()
            if alterno is not None:
                self.visit(alterno[0] if isinstance(alterno, list) else alterno)
            elif len(bloques) > 1:
                self._ejecutar_bloque(bloques[1])
        return None

    def _ejecutar_bloque(self, ctx_bloque):
        if ctx_bloque.sentencias() is not None:
            for sentencia in ctx_bloque.sentencias().sentencia():
                self.visit(sentencia)

    def visitDefinicion_funcion(self, ctx):
        nombre = ctx.identificador().getText()
        parametros = []
        if ctx.parametros() is not None:
            parametros = [p.getText() for p in ctx.parametros().identificador()]
        if len(parametros) != len(set(parametros)):
            raise ErrorSemantico(
                "La funcion '{0}' tiene parametros repetidos.".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        funcion = FuncionArepa(nombre, parametros, ctx.bloque(), self._ambito)
        self._ambito.declarar(nombre, funcion)
        return funcion

    def visitInstruccion_devolver(self, ctx):
        valor = NADA
        if ctx.expresion() is not None:
            valor = self.visit(ctx.expresion())
        raise RetornoFuncion(valor)

    def visitInstruccion_cuenteme(self, ctx):
        valores = []
        if ctx.lista_argumentos() is not None:
            valores = [self.evaluador.evaluar(e) for e in ctx.lista_argumentos().expresion()]
        self.contexto.imprimir(*valores)

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

    def visitInstruccion_llamada(self, ctx):
        return self.evaluador.evaluar(ctx.llamada_funcion())

    # ---------------------------------------------------------------- #
    # Invocacion: funciones del usuario y agregaciones
    # ---------------------------------------------------------------- #

    def _invocar(self, nombre, argumentos, ctx):
        if nombre in AGREGACIONES:
            if not self._en_resuma or self._grupo_filas is None:
                raise ErrorSemantico(
                    "La agregacion '{0}' solo puede usarse dentro de 'resuma'.".format(nombre),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            return self._calcular_agregacion(nombre, argumentos, ctx)

        funcion = self._ambito.buscar_opcional(nombre)
        if isinstance(funcion, FuncionArepa):
            return self._llamar_funcion(funcion, argumentos, ctx)

        raise ErrorSemantico(
            "La funcion '{0}' no existe. Definila con 'invente {0}(...) {{ ... }}' "
            "o usa una agregacion (sume, promedie, ...) dentro de 'resuma'.".format(nombre),
            linea=ctx.start.line,
            columna=ctx.start.column,
        )

    def _llamar_funcion(self, funcion, argumentos, ctx):
        if len(argumentos) != len(funcion.parametros):
            raise ErrorSemantico(
                "La funcion '{0}' recibe {1} parametro(s) ({2}) pero llegaron "
                "{3}.".format(
                    funcion.nombre, len(funcion.parametros),
                    ", ".join(funcion.parametros) or "ninguno", len(argumentos),
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        ambito_llamada = funcion.entorno.hijo()
        for parametro, valor in zip(funcion.parametros, argumentos):
            ambito_llamada.declarar(parametro, valor)

        # Estado guardado: ambito actual y contexto de fila del evaluador.
        ambito_previo = self._ambito
        simbolos_previos = self.evaluador.simbolos
        fila_previa, tabla_previa = self.evaluador._fila, self.evaluador._tabla
        modo_previo = self.evaluador.modo_columna

        self._ambito = ambito_llamada
        self.evaluador.simbolos = ambito_llamada
        self.evaluador._fila, self.evaluador._tabla = None, None
        self.evaluador.modo_columna = False
        try:
            self._ejecutar_bloque(funcion.nodo_bloque)
            return NADA
        except RetornoFuncion as retorno:
            return retorno.valor
        finally:
            self._ambito = ambito_previo
            self.evaluador.simbolos = simbolos_previos
            self.evaluador._fila, self.evaluador._tabla = fila_previa, tabla_previa
            self.evaluador.modo_columna = modo_previo


def _num(valor):
    """Formatea numeros sin '.0' cuando son enteros."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)

