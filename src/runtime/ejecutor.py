"""
AREPA - Ejecutor propio del DSL (src/runtime/ejecutor.py)
---------------------------------------------------------
Implementado por el equipo. Recorre el arbol de analisis generado por
ANTLR4 (uso autorizado) y ejecuta el programa: sentencias, pipeline de
datos, funciones, condicionales, ciclos y agregaciones.

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
  * 'pinte' valida la tabla y sus columnas y construye el PNG con el
    motor propio de graficas (barras, lineas, histograma, dispersion y
    cajas); 'guardela' escribe la ruta pedida y 'muestrela' deja el
    archivo en salidas/ e intenta abrirlo sin bloquear.
  * Lista, Registro y Tabla se crean con literales ([...], {clave: ...},
    arme [...] con [[...]]), se leen con indices 1-based y se modifican
    con 'agregue', 'saque', asignaciones indexadas y 'recorra'.

Decisiones semanticas propias (documentadas):
  * 'deje donde' conserva la fila solo si la condicion es exactamente
    obvio (True); 'nada' y 'falso' descartan la fila;
  * la condicion de 'fijese_si' y de 'mientras' debe ser logica: 'nada'
    es un error;
  * 'repita N veces' exige un entero de 0 en adelante; 'repita i desde
    A hasta B' cuenta con i inclusive (paso 1 o -1 por defecto, o el
    'paso P' indicado, que no puede ser 0);
  * los bloques de ciclos no crean ambito (como 'fijese_si'); la
    variable de 'repita ... desde' queda visible al terminar;
  * 'pare' y 'siga' solo valen dentro de un ciclo; fuera de el son un
    error semantico;
  * 'limpie vacios' sin 'con' elimina las filas con algun 'nada';
  * 'junte' prepara las claves de agrupacion para el 'resuma' siguiente;
  * 'resuma' sin 'junte' previo resume toda la tabla en una sola fila;
  * 'devuelva' fuera de una funcion es un error semantico.
"""

import os
import shutil
import subprocess

from datos import acceso
from datos.escritor_csv import EscritorCSV
from datos.fila import Fila
from datos.lector_csv import LectorCSV
from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import (
    NADA,
    convertir_a_tipo,
    es_nada,
    es_numero,
    formatear_numero,
    nombre_tipo,
)
from errores_base import (
    ErrorColumna,
    ErrorEjecucion,
    ErrorGrafica,
    ErrorOperacion,
    ErrorSemantico,
    ErrorTipos,
    ErrorVariable,
    RetornoFuncion,
    SalirCiclo,
    SeguirCiclo,
)
from expresiones.evaluador import EvaluadorExpresiones
from graficas.tipos_grafica import Serie, dibujar
from runtime.contexto import ContextoEjecucion, a_texto
from runtime.simbolos import FuncionArepa

from ArepaVisitor import ArepaVisitor

AGREGACIONES = (
    "cuente", "sume", "promedie", "mediana", "minimo", "maximo", "desviacion",
)

# Tope de seguridad: un ciclo que da más vueltas casi siempre es un
# descuido (condición que nunca se vuelve falsa o conteo gigante).
# El mensaje pide revisar la condición o el número en vez de colgarse.
MAX_VUELTAS_CICLO = 1000000


class EjecutorArepa(ArepaVisitor):
    """Interpreta el arbol de analisis y produce la ejecucion del programa."""

    def __init__(self):
        self.contexto = ContextoEjecucion()
        self.evaluador = EvaluadorExpresiones(
            self.contexto.simbolos,
            invocar=self._invocar,
            evaluar_expresion=self.evaluar_expresion,
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
        except RecursionError:
            raise ErrorEjecucion(
                "La recursión es muy profunda y se agotó la pila: revisá "
                "el caso base de la función o probá con un número más chico."
            )
        except RetornoFuncion:
            raise ErrorSemantico(
                "'devuelva' solo puede usarse dentro de una función definida "
                "con 'invente'."
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
        EjecutorArepa._exigir_numericos(valores, agregacion, descripcion)
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

    # ---------------------------------------------------------------- #
    # Guardar y graficar
    # ---------------------------------------------------------------- #

    def visitInstruccion_guarde(self, ctx):
        nombre = ctx.identificador().getText()
        ruta = self.evaluador.evaluar(ctx.cadena())
        tabla = self._obtener_tabla(nombre, ctx)
        EscritorCSV().escribir(ruta, tabla)
        self.contexto.registrar_archivo(ruta, "csv", os.path.getsize(ruta))
        self.contexto.imprimir(
            "[guarde] La tabla '{0}' quedo escrita en '{1}' ({2} filas).".format(
                nombre, ruta, tabla.num_filas
            )
        )

    def visitInstruccion_grafica(self, ctx):
        """Ejecuta 'pinte': valida columnas, dibuja el PNG y lo publica.

        Valores por defecto de las columnas (documentados tambien abajo):
          * 'ejex': la primera columna de tipo texto o fecha; si no hay
            ninguna, se usan los indices de fila 1..n como x numerica;
          * 'ejey': todas las columnas numericas de la tabla;
          * 'dispersion' sin 'ejex': la primera columna numerica es x y
            las restantes son las series y (si solo hay una numerica, se
            usa como y y x pasa a ser el indice de fila);
          * 'histograma': exige exactamente una columna en 'ejey' e
            ignora 'ejex', porque las cubetas se calculan sobre los
            valores de y;
          * 'cajas': con 'ejex' textual el motor agrupa una caja por
            categoria; sin x textual hay una caja por serie de 'ejey'.

        La clausula final decide el destino: 'guardela' escribe la ruta
        indicada (obligatoriamente .png), 'muestrela' deja el archivo en
        salidas/<tabla>_<tipo>.png y, si hay entorno grafico, lo abre sin
        esperar. Sin clausula final solo se valida y se renderiza.
        """
        nombre = ctx.identificador().getText()
        tipo = ctx.tipo_grafica().getText()
        tabla = self._obtener_tabla(nombre, ctx)

        if tabla.num_filas == 0:
            raise ErrorGrafica(
                "La tabla '{0}' no tiene filas para graficar.".format(nombre),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        titulo = ""
        leyenda = ""
        columna_x = None
        columnas_y = None
        ubicacion_x = ctx.start
        ubicacion_y = ctx.start
        vistas = set()

        for clausula in ctx.clausula_estetica():
            if clausula.TITULO() is not None:
                self._rechazar_repetida(vistas, "titulo", clausula)
                titulo = self.evaluador.evaluar(clausula.cadena())
            elif clausula.LEYENDA() is not None:
                self._rechazar_repetida(vistas, "leyenda", clausula)
                leyenda = self.evaluador.evaluar(clausula.cadena())
            elif clausula.EJEX() is not None:
                # 'ejex' solo admite una columna, pero se reutiliza el
                # lector de listas para no duplicar logica.
                nombres = self._columnas_de_clausula(clausula)
                columna_x, ubicacion_x = nombres[0]
            elif clausula.EJEY() is not None:
                self._rechazar_repetida(vistas, "ejey", clausula)
                columnas_y = self._columnas_de_clausula(clausula)
                ubicacion_y = clausula.start

        if tipo == "histograma":
            # El histograma ignora 'ejex' a proposito: las cubetas salen
            # de los valores de la unica columna de 'ejey'.
            if columnas_y is None:
                numericas = self._columnas_numericas(tabla)
                if len(numericas) != 1:
                    raise ErrorGrafica(
                        "El histograma necesita exactamente una columna "
                        "numerica en 'ejey' y la tabla '{0}' tiene {1}: {2}. "
                        "Indique una con 'ejey <columna>'.".format(
                            nombre,
                            len(numericas),
                            ", ".join(numericas) if numericas else "ninguna",
                        ),
                        linea=ctx.start.line,
                        columna=ctx.start.column,
                    )
                columnas_y = [(numericas[0], ctx.start)]
            elif len(columnas_y) != 1:
                raise ErrorGrafica(
                    "El histograma usa exactamente una columna en 'ejey'; "
                    "se indicaron {0}: {1}.".format(
                        len(columnas_y),
                        ", ".join(n for n, _ in columnas_y),
                    ),
                    linea=ubicacion_y.line,
                    columna=ubicacion_y.column,
                )
            valores_x = None
            etiqueta_x = ""
            nombre_x = ""
        else:
            if (
                tipo == "dispersion"
                and columna_x is None
                and columnas_y is None
            ):
                numericas = self._columnas_numericas(tabla)
                if not numericas:
                    raise ErrorGrafica(
                        "La dispersion necesita al menos una columna numerica "
                        "en 'ejey'; la tabla '{0}' no tiene ninguna. Columnas: "
                        "{1}.".format(nombre, ", ".join(tabla.nombres_columnas)),
                        linea=ctx.start.line,
                        columna=ctx.start.column,
                    )
                if len(numericas) > 1:
                    columna_x = numericas[0]
                    columnas_y = [(c, ctx.start) for c in numericas[1:]]
                else:
                    # Una sola numerica: no hay par x/y, asi que se usa el
                    # indice de fila como x y esa columna como serie y.
                    columnas_y = [(numericas[0], ctx.start)]

            if columna_x is None:
                nombre_x = self._primera_columna_categorica(tabla)
                if nombre_x is None:
                    valores_x = list(range(1, tabla.num_filas + 1))
                    etiqueta_x = ""
                else:
                    valores_x = tabla.valores_columna(nombre_x)
                    etiqueta_x = nombre_x
            else:
                nombre_x = columna_x
                indice = self._indice_columna(tabla, nombre_x, ubicacion_x, nombre)
                if tipo != "cajas":
                    self._validar_eje_x(tabla, indice, tipo, ubicacion_x)
                valores_x = tabla.valores_columna(nombre_x)
                etiqueta_x = nombre_x

            if columnas_y is None:
                numericas = self._columnas_numericas(tabla)
                if not numericas:
                    raise ErrorGrafica(
                        "La grafica de {0} necesita al menos una columna "
                        "numerica en 'ejey'; la tabla '{1}' no tiene ninguna. "
                        "Columnas: {2}.".format(
                            tipo,
                            nombre,
                            ", ".join(
                                "{0} ({1})".format(c.nombre, c.tipo)
                                for c in tabla.columnas
                            ),
                        ),
                        linea=ctx.start.line,
                        columna=ctx.start.column,
                    )
                columnas_y = [(c, ctx.start) for c in numericas]

        # Cada columna de 'ejey' debe ser numerica: tipo 'numero' o valores
        # todos numericos (los 'nada' se ignoran al dibujar).
        for nombre_y, ubicacion in columnas_y:
            indice = self._indice_columna(tabla, nombre_y, ubicacion, nombre)
            if not self._es_numerica(tabla, indice):
                raise ErrorGrafica(
                    "La grafica de {0} necesita columnas numericas en 'ejey'; "
                    "'{1}' es de tipo {2}. Columnas numericas: {3}.".format(
                        tipo,
                        nombre_y,
                        tabla.columnas[indice].tipo,
                        ", ".join(self._columnas_numericas(tabla))
                        or "ninguna",
                    ),
                    linea=ubicacion.line,
                    columna=ubicacion.column,
                )

        series = [
            Serie(
                nombre=nombre_y,
                x=valores_x,
                y=tabla.valores_columna(nombre_y),
            )
            for nombre_y, _ in columnas_y
        ]

        if leyenda:
            etiqueta_y = leyenda
        elif len(columnas_y) == 1:
            etiqueta_y = columnas_y[0][0]
        else:
            etiqueta_y = ", ".join(nombre_y for nombre_y, _ in columnas_y)

        try:
            lienzo = dibujar(
                tipo,
                series,
                titulo=titulo,
                etiqueta_x=etiqueta_x,
                etiqueta_y=etiqueta_y,
                leyenda=leyenda,
                ancho=800,
                alto=480,
            )
        except ValueError as problema:
            raise ErrorGrafica(
                "No se pudo dibujar la grafica de {0}: {1}".format(
                    tipo, problema
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        final = ctx.final_grafica()
        if final is None:
            self.contexto.imprimir(
                "[pinte] Grafica de {0} sobre '{1}' lista; agregá 'guardela' "
                "o 'muestrela' para verla.".format(tipo, nombre)
            )
            return None

        if final.GUARDELA() is not None:
            ruta = self.evaluador.evaluar(final.cadena())
            if not str(ruta).lower().endswith(".png"):
                raise ErrorGrafica(
                    "La ruta '{0}' debe terminar en '.png' (extension "
                    "esperada para guardar la grafica).".format(ruta),
                    linea=final.start.line,
                    columna=final.start.column,
                )
            escritos = self._guardar_png(lienzo, ruta, final)
            self.contexto.imprimir(
                "[pinte] Grafica de {0} guardada en '{1}' ({2} bytes, "
                "800x480).".format(tipo, ruta, escritos)
            )
        else:
            carpeta = "salidas"
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, "{0}_{1}.png".format(nombre, tipo))
            escritos = self._guardar_png(lienzo, ruta, final)
            self.contexto.imprimir(
                "[pinte] Grafica de {0} en '{1}' ({2} bytes, 800x480).".format(
                    tipo, ruta, escritos
                )
            )
            self._abrir_grafica(ruta)
        return None

    def _rechazar_repetida(self, vistas, clausula, nodo):
        """Falla si 'titulo', 'leyenda' o 'ejey' aparecen dos veces."""
        if clausula in vistas:
            raise ErrorGrafica(
                "La clausula '{0}' esta repetida en la grafica; indiquela "
                "una sola vez.".format(clausula),
                linea=nodo.start.line,
                columna=nodo.start.column,
            )
        vistas.add(clausula)

    @staticmethod
    def _columnas_de_clausula(clausula):
        """Pares (nombre, ubicacion) de 'ejex'/'ejey' (columna o lista)."""
        lista = clausula.lista_literal()
        if lista is None:
            return [(clausula.nombre_columna().getText(), clausula.start)]
        return [
            (expresion.getText().strip(), expresion.start)
            for expresion in lista.expresion()
        ]

    @staticmethod
    def _indice_columna(tabla, nombre, ubicacion, tabla_nombre):
        """Indice de la columna o ErrorColumna con la ubicacion de la clausula."""
        if not tabla.tiene_columna(nombre):
            raise ErrorColumna(
                "La grafica usa la columna '{0}' que no existe en '{1}'. "
                "Columnas: {2}.".format(
                    nombre, tabla_nombre, ", ".join(tabla.nombres_columnas)
                ),
                linea=ubicacion.line,
                columna=ubicacion.column,
            )
        return tabla.indice_columna(nombre)

    @staticmethod
    def _primera_columna_categorica(tabla):
        """Primera columna de tipo texto o fecha, o None."""
        for columna in tabla.columnas:
            if columna.tipo in ("texto", "fecha"):
                return columna.nombre
        return None

    @staticmethod
    def _es_numerica(tabla, indice):
        """True si la columna es 'numero' o todos sus valores son numericos.

        Se aceptan numeros propios y textos que representen un numero
        (el motor de graficas ya convierte esos textos al dibujar).
        """
        columna = tabla.columnas[indice]
        if columna.tipo == "numero":
            return True
        vistos = False
        for valor in tabla.valores_columna(columna.nombre):
            if es_nada(valor):
                continue
            if not EjecutorArepa._es_valor_numerico(valor):
                return False
            vistos = True
        return vistos

    @staticmethod
    def _es_valor_numerico(valor):
        """Numero propio o texto convertible a 'float' no vacio."""
        if es_numero(valor):
            return True
        if not isinstance(valor, str):
            return False
        texto = valor.strip()
        if not texto:
            return False
        try:
            float(texto)
        except ValueError:
            return False
        return True

    def _columnas_numericas(self, tabla):
        """Nombres de las columnas que pueden usarse como 'ejey'."""
        return [
            columna.nombre
            for indice, columna in enumerate(tabla.columnas)
            if self._es_numerica(tabla, indice)
        ]

    @staticmethod
    def _validar_eje_x(tabla, indice, tipo, ubicacion):
        """Valida que x sea numerica o textual (fecha se trata como texto)."""
        columna = tabla.columnas[indice]
        if columna.tipo in ("numero", "texto", "fecha"):
            return
        validas = [
            c.nombre
            for c in tabla.columnas
            if c.tipo in ("numero", "texto", "fecha")
        ]
        raise ErrorGrafica(
            "La grafica de {0} necesita que 'ejex' sea numerica o textual; "
            "'{1}' es de tipo {2}. Columnas validas: {3}.".format(
                tipo,
                columna.nombre,
                columna.tipo,
                ", ".join(validas) or "ninguna",
            ),
            linea=ubicacion.line,
            columna=ubicacion.column,
        )

    def _guardar_png(self, lienzo, ruta, nodo):
        """Escribe el PNG creando directorios y archiva el resultado."""
        carpeta = os.path.dirname(ruta)
        try:
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            escritos = lienzo.guardar(ruta)
        except OSError as problema:
            raise ErrorGrafica(
                "No se pudo escribir el PNG '{0}': {1}".format(ruta, problema),
                linea=nodo.start.line,
                columna=nodo.start.column,
            )
        self.contexto.registrar_archivo(ruta, "png", escritos)
        return escritos

    def _abrir_grafica(self, ruta):
        """Intenta abrir el PNG con xdg-open sin bloquear; nunca falla."""
        sin_ventana = os.environ.get("AREPA_SIN_VENTANA")
        hay_entorno = bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        )
        visor = shutil.which("xdg-open")
        if sin_ventana or not hay_entorno or visor is None:
            self.contexto.imprimir(
                "[pinte] No hay entorno grafico; la imagen quedo en "
                "'{0}'.".format(ruta)
            )
            return
        try:
            subprocess.Popen(
                [visor, ruta],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            self.contexto.imprimir(
                "[pinte] No hay entorno grafico; la imagen quedo en "
                "'{0}'.".format(ruta)
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
                "solo trabaja con tablas cargadas con 'monte' o creadas con "
                "'arme'.".format(nombre, nombre_tipo(valor)),
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

    # ---------------------------------------------------------------- #
    # Ciclos 'mientras' y 'repita' con 'pare' / 'siga'
    # ---------------------------------------------------------------- #
    # Los bloques de un ciclo NO crean ámbito propio (igual que
    # 'fijese_si'): las variables se leen y escriben en el ámbito actual
    # y quedan visibles al terminar el ciclo. 'devuelva' dentro de un
    # ciclo sigue funcionando: RetornoFuncion no se captura aquí y sube
    # hasta la función que lo contiene.

    def visitCiclo_mientras(self, ctx):
        condicion = ctx.expresion_logica()
        bloque = ctx.bloque()
        vueltas = 0
        while True:
            valor = self.evaluador.evaluar(condicion)
            if valor is False:
                break
            if valor is not True:
                raise ErrorTipos(
                    "La condicion de 'mientras' debe ser obvio o falso, pero "
                    "fue {0}.".format(a_texto(valor)),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            vueltas += 1
            if vueltas > MAX_VUELTAS_CICLO:
                raise ErrorEjecucion(
                    "El ciclo 'mientras' dio demasiadas vueltas (más de "
                    "{0}): revisá que la condición pueda volverse falsa.".format(
                        MAX_VUELTAS_CICLO
                    ),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            try:
                self._ejecutar_bloque(bloque)
            except SeguirCiclo:
                continue
            except SalirCiclo:
                break
        return None

    def visitCiclo_repita(self, ctx):
        if ctx.VECES() is not None:
            total = self.evaluador.evaluar(ctx.expresion_logica(0))
            veces = self._exigir_entero_veces(total, ctx)
            if veces > MAX_VUELTAS_CICLO:
                raise ErrorEjecucion(
                    "'repita {0} veces' es demasiado: el tope es {1} "
                    "vueltas.".format(veces, MAX_VUELTAS_CICLO),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            for _ in range(veces):
                try:
                    self._ejecutar_bloque(ctx.bloque())
                except SeguirCiclo:
                    continue
                except SalirCiclo:
                    break
            return None
        return self._ejecutar_repita_rango(ctx)

    def _ejecutar_repita_rango(self, ctx):
        """'repita i desde A hasta B (paso P)': cuenta con i inclusive."""
        nombre = ctx.identificador().getText()
        expresiones = ctx.expresion_logica()
        inicio = self._exigir_numero_ciclo(
            self.evaluador.evaluar(expresiones[0]), ctx, "el inicio"
        )
        fin = self._exigir_numero_ciclo(
            self.evaluador.evaluar(expresiones[1]), ctx, "el fin"
        )
        if len(expresiones) > 2:
            paso = self._exigir_numero_ciclo(
                self.evaluador.evaluar(expresiones[2]), ctx, "el paso"
            )
            if paso == 0:
                raise ErrorSemantico(
                    "El paso de 'repita' no puede ser 0: el ciclo nunca "
                    "avanzaría.",
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
        elif inicio <= fin:
            paso = 1
        else:
            paso = -1

        actual = inicio
        vueltas = 0
        while (actual <= fin) if paso > 0 else (actual >= fin):
            vueltas += 1
            if vueltas > MAX_VUELTAS_CICLO:
                raise ErrorEjecucion(
                    "El ciclo 'repita' dio demasiadas vueltas (más de "
                    "{0}): revisá el rango o el paso.".format(
                        MAX_VUELTAS_CICLO
                    ),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            self._asignar_variable(nombre, actual)
            romper = False
            try:
                self._ejecutar_bloque(ctx.bloque())
            except SeguirCiclo:
                pass
            except SalirCiclo:
                romper = True
            actual = actual + paso
            if romper:
                break
        return None

    def _asignar_variable(self, nombre, valor):
        """Asigna si existe (semántica de 'x = ...') o declara si es nueva."""
        if self._ambito.existe(nombre):
            self._ambito.asignar(nombre, valor)
        else:
            self._ambito.declarar(nombre, valor)
        return valor

    def _exigir_numero_ciclo(self, valor, ctx, papel):
        """Valida un límite de 'repita': debe ser un número (no nada)."""
        if es_nada(valor):
            raise ErrorSemantico(
                "{0} de 'repita' es 'nada': se necesita un número.".format(
                    papel.capitalize()
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not es_numero(valor):
            raise ErrorTipos(
                "{0} de 'repita' debe ser un número, pero fue de tipo "
                "{1}.".format(papel.capitalize(), nombre_tipo(valor)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return valor

    def _exigir_entero_veces(self, valor, ctx):
        """Valida el conteo de 'repita N veces': entero de 0 en adelante."""
        if es_nada(valor):
            raise ErrorSemantico(
                "El conteo de 'repita' es 'nada': se necesita un número "
                "entero de 0 en adelante.",
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ErrorTipos(
                "'repita' necesita un número entero de veces (p. ej. "
                "'repita 5 veces'), pero fue de tipo {0}.".format(
                    nombre_tipo(valor)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if valor < 0:
            raise ErrorSemantico(
                "'repita {0} veces' no es válido: el conteo empieza en 0.".format(
                    valor
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return valor

    def visitInstruccion_pare(self, ctx):
        raise SalirCiclo(linea=ctx.start.line, columna=ctx.start.column)

    def visitInstruccion_siga(self, ctx):
        raise SeguirCiclo(linea=ctx.start.line, columna=ctx.start.column)

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
            valores = [self.visit(e) for e in ctx.lista_argumentos().expresion()]
        self.contexto.imprimir(*valores)

    def visitInstruccion_describa(self, ctx):
        nombre = ctx.identificador().getText()
        tabla = self._obtener_tabla(nombre, ctx)
        self.contexto.imprimir(self._resumen_texto(tabla))

    # ---------------------------------------------------------------- #
    # 'agregue', 'saque' y 'recorra'
    # ---------------------------------------------------------------- #

    def visitInstruccion_agregue(self, ctx):
        nombre = ctx.identificador().getText()
        destino = self._ambito.buscar_opcional(nombre)
        if destino is None:
            raise ErrorVariable(
                "La variable '{0}' no esta declarada; no hay donde agregar.".format(
                    nombre
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        valor = self.visit(ctx.expresion())
        if isinstance(destino, Tabla):
            valores = acceso.valores_para_fila(
                destino, valor, ctx.start.line, ctx.start.column
            )
            destino.insertar_fila(valores)
        elif isinstance(destino, Lista):
            destino.agregar(valor)
        else:
            raise ErrorTipos(
                "'agregue' solo trabaja sobre una tabla o una lista, pero "
                "'{0}' es de tipo {1}.".format(nombre, nombre_tipo(destino)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return None

    def visitInstruccion_saque(self, ctx):
        nombre = ctx.identificador().getText()
        destino = self._ambito.buscar_opcional(nombre)
        if destino is None:
            raise ErrorVariable(
                "La variable '{0}' no esta declarada; no hay de donde sacar.".format(
                    nombre
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        posicion = self.visit(ctx.expresion())
        if not isinstance(posicion, int) or isinstance(posicion, bool):
            raise ErrorTipos(
                "'saque' necesita un numero entero que indique la posicion "
                "(se cuenta desde 1), pero recibio un valor de tipo {0}.".format(
                    nombre_tipo(posicion)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if isinstance(destino, Tabla):
            self._validar_posicion(
                posicion, destino.num_filas, "fila", "La tabla '{0}'".format(nombre),
                ctx,
            )
            destino.eliminar_fila(posicion - 1)
        elif isinstance(destino, Lista):
            self._validar_posicion(
                posicion, destino.largo(), "elemento", "La lista '{0}'".format(nombre),
                ctx,
            )
            destino.quitar(posicion - 1)
        else:
            raise ErrorTipos(
                "'saque' solo trabaja sobre una tabla o una lista, pero "
                "'{0}' es de tipo {1}.".format(nombre, nombre_tipo(destino)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return None

    def _validar_posicion(self, posicion, total, unidad, sujeto, ctx):
        """Valida 1 <= posicion <= total para 'saque' (mensaje 1-based)."""
        if posicion < 1 or posicion > total:
            raise ErrorOperacion(
                "{0} tiene {1} {2}s; no existe {3} {4} (se cuenta desde 1).".format(
                    sujeto, total, unidad,
                    "la" if unidad == "fila" else "el", posicion,
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

    def visitCiclo_recorra(self, ctx):
        destino = ctx.identificador(0).getText()
        nombre_fuente = ctx.identificador(1).getText()
        fuente = self._ambito.buscar_opcional(nombre_fuente)
        if fuente is None:
            raise ErrorVariable(
                "La variable '{0}' no esta declarada; no hay nada que "
                "recorrer.".format(nombre_fuente),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if isinstance(fuente, Tabla):
            # Snapshot de las filas: si la tabla cambia durante el
            # recorrido, el ciclo sigue sobre las filas iniciales. Cada
            # registro queda enlazado a su fila, así que las mutaciones
            # de celdas sí se reflejan en la tabla.
            elementos = [
                fuente.fila_como_registro(i) for i in range(fuente.num_filas)
            ]
        elif isinstance(fuente, Lista):
            elementos = list(fuente)
        else:
            raise ErrorTipos(
                "'recorra' necesita una tabla o una lista, pero '{0}' es de "
                "tipo {1}.".format(nombre_fuente, nombre_tipo(fuente)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        if len(elementos) > MAX_VUELTAS_CICLO:
            raise ErrorEjecucion(
                "El ciclo 'recorra' tiene {0} elementos y el tope es {1}: "
                "revisá la colección.".format(len(elementos), MAX_VUELTAS_CICLO),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        for elemento in elementos:
            self._asignar_variable(destino, elemento)
            try:
                self._ejecutar_bloque(ctx.bloque())
            except SeguirCiclo:
                continue
            except SalirCiclo:
                break
        return None

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
        return self.visit(ctx.llamada_funcion())

    def visitLlamada_funcion(self, ctx):
        """Una llamada suelta la resuelve el evaluador de expresiones."""
        return self.evaluador.evaluar(ctx)

    # ---------------------------------------------------------------- #
    # Invocacion: funciones del usuario y agregaciones
    # ---------------------------------------------------------------- #

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

    # ---------------------------------------------------------------- #
    # Funciones incorporadas de la Fase A
    # ---------------------------------------------------------------- #

    def _largo(self, argumentos, ctx):
        self._exigir_aridad("largo", argumentos, 1, ctx)
        valor = argumentos[0]
        if isinstance(valor, Tabla):
            return valor.num_filas
        if isinstance(valor, Lista):
            return valor.largo()
        if isinstance(valor, Registro):
            return valor.largo()
        if isinstance(valor, str):
            return len(valor)
        raise ErrorTipos(
            "'largo' no acepta un valor de tipo {0}; espera una tabla, una "
            "lista, un registro o un texto.".format(nombre_tipo(valor)),
            linea=ctx.start.line,
            columna=ctx.start.column,
        )

    def _columna(self, argumentos, ctx):
        self._exigir_aridad("columna", argumentos, 2, ctx)
        tabla, columna = argumentos
        if not isinstance(tabla, Tabla):
            raise ErrorTipos(
                "El primer argumento de 'columna' debe ser una tabla, pero "
                "llegó un valor de tipo {0}.".format(nombre_tipo(tabla)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(columna, str):
            raise ErrorTipos(
                "El segundo argumento de 'columna' debe ser el nombre de una "
                "columna, pero llegó un valor de tipo {0}.".format(
                    nombre_tipo(columna)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        try:
            valores = tabla.valores_columna(columna)
        except ErrorColumna as problema:
            if problema.linea == -1:
                problema.linea = ctx.start.line
                problema.columna = ctx.start.column
            raise
        return Lista(valores)

    def _columnas(self, argumentos, ctx):
        self._exigir_aridad("columnas", argumentos, 1, ctx)
        tabla = argumentos[0]
        if not isinstance(tabla, Tabla):
            raise ErrorTipos(
                "'columnas' espera una tabla, pero llegó un valor de tipo "
                "{0}.".format(nombre_tipo(tabla)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        return Lista(tabla.nombres_columnas)

    def _exigir_aridad(self, nombre, argumentos, esperados, ctx):
        if len(argumentos) != esperados:
            raise ErrorSemantico(
                "'{0}' recibe {1} argumento(s) pero llegaron {2}.".format(
                    nombre, esperados, len(argumentos)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

    # ---------------------------------------------------------------- #
    # Agregaciones fuera de 'resuma'
    # ---------------------------------------------------------------- #

    def _agregacion_fuera_de_resuma(self, nombre, argumentos, ctx):
        """Agregacion sobre una tabla+columna o sobre una lista."""
        if nombre == "cuente":
            if len(argumentos) == 1:
                valor = argumentos[0]
                if isinstance(valor, Tabla):
                    return valor.num_filas
                if isinstance(valor, Lista):
                    return valor.largo()
                raise ErrorTipos(
                    "'cuente' espera una tabla o una lista, pero llegó un "
                    "valor de tipo {0}.".format(nombre_tipo(valor)),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            if len(argumentos) == 2:
                tabla, columna = argumentos
                self._exigir_tabla_y_columna(nombre, tabla, columna, ctx)
                indice = self._indice_de_columna(tabla, columna, ctx)
                return sum(
                    1 for f in tabla.filas if not es_nada(f.valor_en(indice))
                )
            raise ErrorSemantico(
                "'cuente' necesita una tabla, una lista o una tabla y una "
                "columna: cuente(tabla), cuente(lista) o cuente(tabla, columna).",
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

        if len(argumentos) == 1:
            valor = argumentos[0]
            if not isinstance(valor, Lista):
                raise ErrorTipos(
                    "La agregacion '{0}' espera una lista o '{0}(tabla, "
                    "columna)', pero llegó un valor de tipo {1}.".format(
                        nombre, nombre_tipo(valor)
                    ),
                    linea=ctx.start.line,
                    columna=ctx.start.column,
                )
            return self._calcular_sobre_valores(nombre, list(valor), "la lista")

        if len(argumentos) == 2:
            tabla, columna = argumentos
            self._exigir_tabla_y_columna(nombre, tabla, columna, ctx)
            self._indice_de_columna(tabla, columna, ctx)
            return self._calcular_sobre_valores(
                nombre, tabla.valores_columna(columna),
                "la columna '{0}'".format(columna),
            )

        raise ErrorSemantico(
            "La agregacion '{0}' necesita una lista o una tabla y una "
            "columna: {0}(lista) o {0}(tabla, columna).".format(nombre),
            linea=ctx.start.line,
            columna=ctx.start.column,
        )

    def _exigir_tabla_y_columna(self, nombre, tabla, columna, ctx):
        if not isinstance(tabla, Tabla):
            raise ErrorTipos(
                "El primer argumento de '{0}' debe ser una tabla, pero llegó "
                "un valor de tipo {1}.".format(nombre, nombre_tipo(tabla)),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )
        if not isinstance(columna, str):
            raise ErrorTipos(
                "El segundo argumento de '{0}' debe ser el nombre de una "
                "columna, pero llegó un valor de tipo {1}.".format(
                    nombre, nombre_tipo(columna)
                ),
                linea=ctx.start.line,
                columna=ctx.start.column,
            )

    def _indice_de_columna(self, tabla, columna, ctx):
        try:
            return tabla.indice_columna(columna)
        except ErrorColumna as problema:
            if problema.linea == -1:
                problema.linea = ctx.start.line
                problema.columna = ctx.start.column
            raise

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
        contexto_fila_previo = self.evaluador.tomar_contexto_fila()

        self._ambito = ambito_llamada
        self.evaluador.simbolos = ambito_llamada
        self.evaluador.fijar_contexto_fila(None, None, False)
        try:
            self._ejecutar_bloque(funcion.nodo_bloque)
            return NADA
        except RetornoFuncion as retorno:
            return retorno.valor
        finally:
            self._ambito = ambito_previo
            self.evaluador.simbolos = simbolos_previos
            self.evaluador.fijar_contexto_fila(*contexto_fila_previo)


def _num(valor):
    """Formatea numeros sin '.0' cuando son enteros; infinitos como 'infinito'."""
    return formatear_numero(valor)

