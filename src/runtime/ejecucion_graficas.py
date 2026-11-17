"""Visitor: operaciones de graficas.

Mixin sin estado independiente; EjecutorArepa aporta contexto, símbolos y
evaluador. Las operaciones siguen recorriendo el árbol ANTLR real.
"""

import os
import shutil
import subprocess
from datos.tipos import es_nada, es_numero
from errores_base import ErrorColumna, ErrorGrafica
from graficas.tipos_grafica import Serie, dibujar

class EjecucionGraficas:
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
            if not EjecucionGraficas._es_valor_numerico(valor):
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
