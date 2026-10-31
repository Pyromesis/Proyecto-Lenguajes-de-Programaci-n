"""Biblioteca propia de datos del DSL AREPA (implementada desde cero).

Reexporta las estructuras centrales para que el runtime pueda importarlas
desde un solo lugar: Tabla (con Filas y Columnas), Lista y Registro.
Ninguna de ellas usa pandas, numpy, csv ni dict para el almacenamiento.
"""

from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla

__all__ = ["Lista", "Registro", "Tabla"]
