"""
AREPA - Preprocesamiento propio para machine learning (src/ml/preprocesamiento.py)
----------------------------------------------------------------------------------
Implementado por el equipo desde cero. Convierte una Tabla del DSL en
matrices de números que los algoritmos propios pueden consumir.

Qué hace:
  * valida que las columnas de entrada existan y que el objetivo exista;
  * imputa faltantes: media en columnas numéricas y moda en categóricas;
  * codifica columnas categóricas con one-hot encoding propio;
  * estandariza columnas numéricas (media 0, desviación 1) cuando el
    algoritmo lo necesita (regresión y perceptrón);
  * conserva las categorías y estadísticas para transformar tablas nuevas
    con exactamente la misma codificación.

Decisiones:
  * una columna con valores numéricos y lógicos se trata como numérica;
  * las fechas y los textos se tratan como categóricos;
  * una categoría desconocida en predicción se codifica como un vector
    one-hot de ceros (no rompe la predicción);
  * las filas con el objetivo vacío se descartan del entrenamiento.
"""

from datos.tipos import es_logico, es_nada, es_numero
from errores_base import ErrorColumna, ErrorSemantico, ErrorTipos


class InfoColumna:
    """Estadísticas y codificación aprendidas para una columna de entrada."""

    __slots__ = (
        "nombre",
        "tipo",
        "media",
        "desviacion",
        "moda",
        "categorias",
        "indice_categoria",
    )

    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo = tipo
        self.media = 0.0
        self.desviacion = 1.0
        self.moda = None
        self.categorias = []
        self.indice_categoria = {}


class Preprocesador:
    """Aprende la codificación de las columnas y transforma filas nuevas."""

    def __init__(self, tabla, columnas, objetivo):
        self.columnas = list(columnas)
        self.objetivo = objetivo
        self.infos = []
        self.nombres_features = []
        self.dimension = 0
        self._ajustar(tabla)

    # ---------------------------------------------------------------- #
    # Aprendizaje de la codificación
    # ---------------------------------------------------------------- #

    def _ajustar(self, tabla):
        if not self.columnas:
            raise ErrorSemantico(
                "'entrene' necesita al menos una columna de entrada en "
                "'columnas [...]'."
            )
        if len(set(self.columnas)) != len(self.columnas):
            raise ErrorSemantico(
                "La lista 'columnas' tiene nombres repetidos: {0}.".format(
                    ", ".join(self.columnas)
                )
            )
        if self.objetivo in self.columnas:
            raise ErrorSemantico(
                "La columna objetivo '{0}' no puede estar también en "
                "'columnas': el modelo no puede usar la respuesta como pista.".format(
                    self.objetivo
                )
            )
        if not tabla.tiene_columna(self.objetivo):
            raise ErrorColumna(
                "La columna objetivo '{0}' no existe en la tabla '{1}'. "
                "Columnas disponibles: {2}.".format(
                    self.objetivo, tabla.nombre, ", ".join(tabla.nombres_columnas)
                )
            )

        for nombre in self.columnas:
            if not tabla.tiene_columna(nombre):
                raise ErrorColumna(
                    "La columna de entrada '{0}' no existe en la tabla '{1}'. "
                    "Columnas disponibles: {2}.".format(
                        nombre, tabla.nombre, ", ".join(tabla.nombres_columnas)
                    )
                )
            info = self._aprender_columna(tabla, nombre)
            self.infos.append(info)
            if info.tipo == "numerica":
                self.nombres_features.append(info.nombre)
                self.dimension += 1
            else:
                for categoria in info.categorias:
                    self.nombres_features.append(
                        "{0}={1}".format(info.nombre, _texto_categoria(categoria))
                    )
                self.dimension += len(info.categorias)

    def _aprender_columna(self, tabla, nombre):
        valores = tabla.valores_columna(nombre)
        presentes = [v for v in valores if not es_nada(v)]
        if not presentes:
            raise ErrorSemantico(
                "La columna de entrada '{0}' está vacía: no hay valores para "
                "aprender.".format(nombre)
            )

        if all(es_numero(v) or es_logico(v) for v in presentes):
            info = InfoColumna(nombre, "numerica")
            numeros = [_a_numero(v) for v in presentes]
            info.media = sum(numeros) / len(numeros)
            varianza = sum((v - info.media) ** 2 for v in numeros) / len(numeros)
            info.desviacion = varianza ** 0.5
            if info.desviacion == 0:
                info.desviacion = 1.0
            return info

        info = InfoColumna(nombre, "categorica")
        info.categorias = _categorias_unicas(presentes)
        info.indice_categoria = {
            categoria: i for i, categoria in enumerate(info.categorias)
        }
        info.moda = _moda(presentes)
        return info

    # ---------------------------------------------------------------- #
    # Transformación de filas y tablas
    # ---------------------------------------------------------------- #

    def transformar_fila(self, fila, tabla, estandarizar=False):
        """Devuelve el vector numérico de una fila usando la codificación aprendida."""
        vector = []
        for info in self.infos:
            indice = tabla.indice_columna(info.nombre)
            valor = fila.valor_en(indice)
            if info.tipo == "numerica":
                numero = info.media if es_nada(valor) else _a_numero(valor)
                if estandarizar:
                    numero = (numero - info.media) / info.desviacion
                vector.append(numero)
            else:
                categoria = info.moda if es_nada(valor) else valor
                posicion = info.indice_categoria.get(categoria)
                for i in range(len(info.categorias)):
                    vector.append(1.0 if posicion == i else 0.0)
        return vector

    def transformar_tabla(self, tabla, estandarizar=False):
        """Transforma todas las filas de una tabla en una lista de vectores."""
        return [
            self.transformar_fila(fila, tabla, estandarizar) for fila in tabla.filas
        ]

    def datos(self, tabla, estandarizar=False):
        """Devuelve (X, y) descartando las filas cuyo objetivo es 'nada'.

        También valida que el objetivo no sea vacío y que las columnas de
        entrada sigan existiendo en la tabla recibida.
        """
        if not tabla.tiene_columna(self.objetivo):
            raise ErrorColumna(
                "La tabla '{0}' no tiene la columna objetivo '{1}'. Columnas: "
                "{2}.".format(
                    tabla.nombre, self.objetivo, ", ".join(tabla.nombres_columnas)
                )
            )
        for nombre in self.columnas:
            if not tabla.tiene_columna(nombre):
                raise ErrorColumna(
                    "La tabla '{0}' no tiene la columna de entrada '{1}'. "
                    "Columnas: {2}.".format(
                        tabla.nombre, nombre, ", ".join(tabla.nombres_columnas)
                    )
                )

        indice_objetivo = tabla.indice_columna(self.objetivo)
        X = []
        y = []
        for fila in tabla.filas:
            valor = fila.valor_en(indice_objetivo)
            if es_nada(valor):
                continue
            X.append(self.transformar_fila(fila, tabla, estandarizar))
            y.append(valor)
        if not X:
            raise ErrorSemantico(
                "No quedaron filas para entrenar: todas tienen 'nada' en la "
                "columna objetivo '{0}'.".format(self.objetivo)
            )
        return X, y

    def resumen(self):
        """Texto corto con la codificación aprendida."""
        partes = []
        for info in self.infos:
            if info.tipo == "numerica":
                partes.append(
                    "{0}: numérica (media={1}, desviación={2})".format(
                        info.nombre,
                        _numero_texto(info.media),
                        _numero_texto(info.desviacion),
                    )
                )
            else:
                partes.append(
                    "{0}: categórica ({1})".format(
                        info.nombre,
                        ", ".join(_texto_categoria(c) for c in info.categorias),
                    )
                )
        return "; ".join(partes)


# ---------------------------------------------------------------------- #
# Utilidades propias (sin statistics, numpy ni pandas)
# ---------------------------------------------------------------------- #

def _a_numero(valor):
    if es_logico(valor):
        return 1.0 if valor else 0.0
    if es_numero(valor):
        return float(valor)
    raise ErrorTipos(
        "La columna numérica contiene un valor que no es número: {0}.".format(valor)
    )


def _categorias_unicas(valores):
    vistas = []
    conocidas = set()
    for valor in valores:
        if valor not in conocidas:
            conocidas.add(valor)
            vistas.append(valor)
    return vistas


def _moda(valores):
    conteo = {}
    orden = []
    for valor in valores:
        if valor not in conteo:
            conteo[valor] = 0
            orden.append(valor)
        conteo[valor] += 1
    return max(orden, key=lambda v: conteo[v])


def _texto_categoria(valor):
    if es_logico(valor):
        return "obvio" if valor else "falso"
    return str(valor)


def _numero_texto(valor):
    valor = round(float(valor), 4)
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)
