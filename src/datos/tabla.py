"""
AREPA - Tabla propia (src/datos/tabla.py)
-----------------------------------------
Implementado por el equipo. Estructura de datos central del DSL: el
equivalente propio a un marco de datos, sin usar pandas ni bibliotecas
similares. Consta de:
  * columnas: lista de Columna (nombre + tipo);
  * filas: lista de Fila con los valores en el mismo orden;
  * metadatos: nombre de la tabla y archivo de origen.

Operaciones implementadas manualmente (recorren filas y columnas):
  seleccionar, filtrar, ordenar (mezcla propia), crear columna,
  renombrar, quitar duplicados, tratar vacíos, convertir tipos,
  agrupar y utilidades de formato.

Decisiones propias documentadas:
  * el ordenamiento es estable y coloca los 'nada' al final;
  * 'quitar_duplicados' conserva la primera aparición de cada fila;
  * 'agrupar' conserva el orden de primera aparición de las claves.

Limitaciones:
  * las operaciones copian la lista de filas (no hay vistas perezosas);
  * no hay índices ni optimizaciones: todo es recorrido lineal.
"""

from datos.columna import Columna
from datos.fila import Fila
from errores_base import ErrorColumna
from datos.tipos import es_nada, nombre_tipo


class Tabla:
    """Conjunto de datos propio: columnas con nombre y filas de valores."""

    def __init__(self, nombres_columnas, filas=None, nombre="tabla", origen=""):
        if not nombres_columnas:
            raise ValueError("Una tabla necesita al menos una columna.")
        self.columnas = [Columna(n) for n in nombres_columnas]
        self.filas = list(filas) if filas else []
        self.nombre = nombre
        self.origen = origen
        self._inferir_tipos()

    # ---------------------------------------------------------------- #
    # Metadatos básicos
    # ---------------------------------------------------------------- #

    @property
    def nombres_columnas(self):
        return [c.nombre for c in self.columnas]

    @property
    def num_filas(self):
        return len(self.filas)

    def _inferir_tipos(self):
        for i, columna in enumerate(self.columnas):
            valores = [f.valor_en(i) for f in self.filas]
            columna.tipo = Columna.inferir(columna.nombre, valores).tipo

    def indice_columna(self, nombre):
        """Posición de una columna; ErrorColumna si no existe."""
        for i, columna in enumerate(self.columnas):
            if columna.nombre == nombre:
                return i
        raise ErrorColumna(
            "La columna '{0}' no existe en la tabla '{1}'. Columnas disponibles: {2}.".format(
                nombre, self.nombre, ", ".join(self.nombres_columnas)
            )
        )

    def valores_columna(self, nombre):
        """Lista con los valores de una columna, fila por fila."""
        i = self.indice_columna(nombre)
        return [f.valor_en(i) for f in self.filas]

    # ---------------------------------------------------------------- #
    # Selección
    # ---------------------------------------------------------------- #

    def seleccionar(self, nombres):
        """Nueva tabla solo con las columnas pedidas, en ese orden."""
        indices = [self.indice_columna(n) for n in nombres]
        nuevas_filas = [
            Fila([f.valor_en(i) for i in indices]) for f in self.filas
        ]
        return Tabla(nombres, nuevas_filas, self.nombre, self.origen)

    # ---------------------------------------------------------------- #
    # Filtrado: 'predicado' es una función propia fila -> bool
    # ---------------------------------------------------------------- #

    def filtrar(self, predicado):
        """Nueva tabla con las filas cuyo predicado devuelve True."""
        quedan = [f.copiar() for f in self.filas if predicado(f) is True]
        resultado = Tabla(self.nombres_columnas, quedan, self.nombre, self.origen)
        for c, original in zip(resultado.columnas, self.columnas):
            c.tipo = original.tipo
        return resultado

    # ---------------------------------------------------------------- #
    # Ordenamiento con mezcla propia (merge sort estable)
    # ---------------------------------------------------------------- #

    def ordenar(self, claves):
        """Ordena por [(nombre_columna, direccion)] con mezcla propia.

        direccion es 'pa_arriba' (ascendente) o 'pa_abajo' (descendente).
        Los valores 'nada' siempre quedan al final.
        """
        if not claves:
            raise ValueError("acomode necesita al menos una columna.")
        criterios = [(self.indice_columna(n), d) for n, d in claves]
        ordenadas = self._mezcla(self.filas, criterios)
        resultado = Tabla(self.nombres_columnas, ordenadas, self.nombre, self.origen)
        for c, original in zip(resultado.columnas, self.columnas):
            c.tipo = original.tipo
        return resultado

    def _mezcla(self, filas, criterios):
        cantidad = len(filas)
        if cantidad <= 1:
            return list(filas)
        medio = cantidad // 2
        izquierda = self._mezcla(filas[:medio], criterios)
        derecha = self._mezcla(filas[medio:], criterios)
        return self._fusionar(izquierda, derecha, criterios)

    @staticmethod
    def _fusionar(izquierda, derecha, criterios):
        resultado = []
        i = j = 0
        while i < len(izquierda) and j < len(derecha):
            if Tabla._menor(izquierda[i], derecha[j], criterios):
                resultado.append(izquierda[i])
                i += 1
            else:
                resultado.append(derecha[j])
                j += 1
        resultado.extend(izquierda[i:])
        resultado.extend(derecha[j:])
        return resultado

    @staticmethod
    def _menor(fila_a, fila_b, criterios):
        """¿Va 'a' estrictamente antes que 'b' según los criterios?

        El 'nada' se considera mayor que cualquier valor (queda al final)
        y dos 'nada' se consideran iguales entre sí.
        """
        for indice, direccion in criterios:
            a = fila_a.valor_en(indice)
            b = fila_b.valor_en(indice)
            if es_nada(a) and es_nada(b):
                continue
            if es_nada(a):
                return False
            if es_nada(b):
                return True
            if a == b:
                continue
            if isinstance(a, str) == isinstance(b, str):
                menor = a < b
            else:
                menor = str(a) < str(b)
            if direccion == "pa_abajo":
                return not menor
            return menor
        return False

    # ---------------------------------------------------------------- #
    # Creación, renombre y eliminación de columnas
    # ---------------------------------------------------------------- #

    def crear_columna(self, nombre, funcion_valor):
        """Agrega una columna calculando cada celda con 'funcion_valor(fila)'."""
        if self._indice_opcional(nombre) is not None:
            raise ErrorColumna(
                "La columna '{0}' ya existe en '{1}'; no se puede crear de nuevo.".format(
                    nombre, self.nombre
                )
            )
        for f in self.filas:
            f.agregar(funcion_valor(f))
        self.columnas.append(Columna(nombre))
        self.columnas[-1].tipo = Columna.inferir(
            nombre, self.valores_columna(nombre)
        ).tipo

    def renombrar(self, viejo, nuevo):
        """Cambia el nombre de una columna conservando su posición."""
        if viejo != nuevo and self._indice_opcional(nuevo) is not None:
            raise ErrorColumna(
                "No puedo renombrar '{0}' a '{1}': ya existe una columna con ese nombre.".format(
                    viejo, nuevo
                )
            )
        indice = self.indice_columna(viejo)
        self.columnas[indice].nombre = nuevo

    def eliminar_columna(self, nombre):
        """Quita una columna y su valor en cada fila."""
        indice = self.indice_columna(nombre)
        del self.columnas[indice]
        for f in self.filas:
            del f.valores[indice]

    def tiene_columna(self, nombre):
        """True si existe una columna con ese nombre."""
        return self._indice_opcional(nombre) is not None

    def _indice_opcional(self, nombre):
        for i, columna in enumerate(self.columnas):
            if columna.nombre == nombre:
                return i
        return None

    # ---------------------------------------------------------------- #
    # Tratamiento de duplicados y vacíos
    # ---------------------------------------------------------------- #

    def quitar_duplicados(self):
        """Elimina filas repetidas conservando la primera aparición."""
        vistas = set()
        quedan = []
        for f in self.filas:
            clave = tuple(f.valores)
            if clave not in vistas:
                vistas.add(clave)
                quedan.append(f)
        self.filas = quedan

    def rellenar_vacios(self, valor, columna=None):
        """Reemplaza los 'nada' por 'valor' (en una columna o en todas)."""
        if columna is not None:
            i = self.indice_columna(columna)
            for f in self.filas:
                if es_nada(f.valor_en(i)):
                    f.poner_en(i, valor)
        else:
            for f in self.filas:
                for i, v in enumerate(f.valores):
                    if es_nada(v):
                        f.poner_en(i, valor)

    def eliminar_filas_con_vacios(self):
        """Quita las filas que tengan algún 'nada'."""
        self.filas = [
            f for f in self.filas if all(not es_nada(v) for v in f.valores)
        ]

    # ---------------------------------------------------------------- #
    # Conversión de tipos
    # ---------------------------------------------------------------- #

    def convertir_columna(self, nombre, tipo, convertir_celda):
        """Convierte una columna con la función propia 'convertir_celda'.

        'convertir_celda(valor, contexto)' la aporta el sistema de tipos;
        si una celda no se puede convertir, la excepción incluye la fila.
        """
        i = self.indice_columna(nombre)
        for n, f in enumerate(self.filas, 1):
            f.poner_en(i, convertir_celda(f.valor_en(i), "fila {0}".format(n)))
        self.columnas[i].tipo = tipo

    # ---------------------------------------------------------------- #
    # Agrupamiento propio
    # ---------------------------------------------------------------- #

    def agrupar(self, nombres):
        """Agrupa las filas por los valores de las columnas dadas.

        Devuelve una lista de (valores_clave, filas_del_grupo) conservando
        el orden de primera aparición de cada clave.
        """
        indices = [self.indice_columna(n) for n in nombres]
        grupos = {}
        orden = []
        for f in self.filas:
            clave = tuple(f.valor_en(i) for i in indices)
            if clave not in grupos:
                grupos[clave] = []
                orden.append(clave)
            grupos[clave].append(f)
        return [(clave, grupos[clave]) for clave in orden]

    # ---------------------------------------------------------------- #
    # Utilidades
    # ---------------------------------------------------------------- #

    def copiar(self):
        copia = Tabla(self.nombres_columnas, [f.copiar() for f in self.filas],
                      self.nombre, self.origen)
        return copia

    def texto_tabla(self, maximo_filas=10):
        """Representación propia en texto (reemplaza a tabulate/pandas).

        Calcula el ancho de cada columna con sus valores visibles y
        recorta la lista de filas si hay demasiadas.
        """
        celdas = [list(self.nombres_columnas)]
        for f in self.filas[:maximo_filas]:
            celdas.append([_visible(v) for v in f.valores])
        anchos = [
            max(len(celdas[f][c]) for f in range(len(celdas)))
            for c in range(len(self.nombres_columnas))
        ]
        lineas = []
        for n, fila_texto in enumerate(celdas):
            linea = " | ".join(
                fila_texto[c].ljust(anchos[c]) for c in range(len(anchos))
            )
            lineas.append(linea)
            if n == 0:
                lineas.append("-+-".join("-" * a for a in anchos))
        if self.num_filas > maximo_filas:
            lineas.append("... ({0} filas más)".format(self.num_filas - maximo_filas))
        return "\n".join(lineas)


def _visible(valor):
    """Texto de una celda para mostrar (los 'nada' se ven como 'nada')."""
    if es_nada(valor):
        return "nada"
    if isinstance(valor, bool):
        return "obvio" if valor else "falso"
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


# 'nombre_tipo' se reexporta para que los mensajes de la tabla usen el
# vocabulario del DSL sin repetir la importación en cada módulo cliente.
__all__ = ["Tabla", "Fila", "Columna", "nombre_tipo"]
