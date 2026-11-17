"""Visitor: operaciones de control.

Mixin sin estado independiente; EjecutorArepa aporta contexto, símbolos y
evaluador. Las operaciones siguen recorriendo el árbol ANTLR real.
"""

from datos.lista import Lista
from datos.tabla import Tabla
from datos.tipos import NADA, es_nada, es_numero, nombre_tipo
from errores_base import (
    ErrorArepa,
    ErrorEjecucion,
    ErrorSemantico,
    ErrorTipos,
    ErrorVariable,
    RetornoFuncion,
    SalirCiclo,
    SeguirCiclo,
)
from runtime.contexto import a_texto
from runtime.simbolos import FuncionArepa

class EjecucionControl:
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
            if vueltas > self.limite_vueltas:
                raise ErrorEjecucion(
                    "El ciclo 'mientras' dio demasiadas vueltas (más de "
                    "{0}): revisá que la condición pueda volverse falsa.".format(
                        self.limite_vueltas
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
            if veces > self.limite_vueltas:
                raise ErrorEjecucion(
                    "'repita {0} veces' es demasiado: el tope es {1} "
                    "vueltas.".format(veces, self.limite_vueltas),
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
            if vueltas > self.limite_vueltas:
                raise ErrorEjecucion(
                    "El ciclo 'repita' dio demasiadas vueltas (más de "
                    "{0}): revisá el rango o el paso.".format(
                        self.limite_vueltas
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

        if len(elementos) > self.limite_vueltas:
            raise ErrorEjecucion(
                "El ciclo 'recorra' tiene {0} elementos y el tope es {1}: "
                "revisá la colección.".format(len(elementos), self.limite_vueltas),
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
        except ErrorArepa as problema:
            if len(problema.llamadas) < 5:
                problema.llamadas.append((funcion.nombre, ctx.start.line, ctx.start.column))
            raise
        finally:
            self._ambito = ambito_previo
            self.evaluador.simbolos = simbolos_previos
            self.evaluador.fijar_contexto_fila(*contexto_fila_previo)
