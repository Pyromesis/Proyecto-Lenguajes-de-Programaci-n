"""Visitor: operaciones de estructuras.

Mixin sin estado independiente; EjecutorArepa aporta contexto, símbolos y
evaluador. Las operaciones siguen recorriendo el árbol ANTLR real.
"""

from datos import acceso
from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import es_nada, nombre_tipo
from errores_base import ErrorColumna, ErrorOperacion, ErrorSemantico, ErrorTipos, ErrorVariable

class EjecucionEstructuras:
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
