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

from datos.tipos import es_infinito, es_nada, formatear_numero, texto_a_valor, es_numero


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
            # Una fila con una sola celda nada no puede confundirse con una
            # línea vacía, que el lector ignora. El texto "nada" se cita.
            texto = "nada"
        elif isinstance(valor, bool):
            texto = "obvio" if valor else "falso"
        elif es_infinito(valor):
            texto = formatear_numero(valor)
        elif es_numero(valor):
            texto = formatear_numero(valor)
        else:
            texto = str(valor)
        ambiguo = (isinstance(valor, str) and
                   (not texto or texto != texto.strip() or texto == "nada" or
                    not isinstance(texto_a_valor(texto), str)))
        if (ambiguo or self.separador in texto or '"' in texto or "\n" in texto
                or "\r" in texto):
            texto = '"' + texto.replace('"', '""') + '"'
        return texto
