"""
AREPA - Escritor CSV propio (src/datos/escritor_csv.py)
-------------------------------------------------------
Implementado por el equipo desde cero: escribe tablas propias a archivos
CSV para la instrucción 'guarde ... como ...'.

Qué hace:
  * escribir el encabezado con los nombres de columnas;
  * escribir cada fila con los valores convertidos a texto propio;
  * entrecomillar campos que contengan el separador, comillas o saltos;
  * escapar comillas internas duplicándolas (regla estándar CSV);
  * crear la carpeta destino si no existe (con os.makedirs, que es
    infraestructura del sistema, no lógica de datos).

Limitaciones:
  * siempre escribe UTF-8 sin BOM y separador configurable único.
"""

import os

from datos.tipos import es_nada


class EscritorCSV:
    """Escribe una Tabla propia al formato CSV."""

    def __init__(self, separador=","):
        if len(separador) != 1:
            raise ValueError("El separador debe ser un único carácter.")
        self.separador = separador

    def escribir(self, ruta, tabla):
        carpeta = os.path.dirname(os.path.abspath(ruta))
        os.makedirs(carpeta, exist_ok=True)
        lineas = [self._fila_texto(tabla.nombres_columnas)]
        for f in tabla.filas:
            lineas.append(self._fila_texto(f.valores))
        with open(ruta, "w", encoding="utf-8", newline="") as manejador:
            manejador.write("\n".join(lineas) + "\n")
        return ruta

    def _fila_texto(self, valores):
        return self.separador.join(self._campo_texto(v) for v in valores)

    def _campo_texto(self, valor):
        if es_nada(valor):
            texto = ""
        elif isinstance(valor, bool):
            texto = "obvio" if valor else "falso"
        elif isinstance(valor, float) and valor.is_integer():
            texto = str(int(valor))
        else:
            texto = str(valor)
        if (self.separador in texto or '"' in texto or "\n" in texto
                or "\r" in texto):
            texto = '"' + texto.replace('"', '""') + '"'
        return texto
