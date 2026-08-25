"""
AREPA - Lector CSV propio (src/datos/lector_csv.py)
---------------------------------------------------
Implementado por el equipo desde cero: no usa 'csv', 'pandas' ni
ninguna biblioteca de lectura de datos. Es una máquina de estados que
recorre el archivo carácter a carácter.

Qué hace:
  * abrir archivos de texto (UTF-8, tolera BOM con utf-8-sig);
  * detectar encabezados o generar nombres automáticos (columna_1...);
  * separar campos respetando comillas dobles;
  * aceptar el separador dentro de comillas y el escape "" como comilla;
  * ignorar líneas vacías;
  * convertir cada campo con el sistema propio de tipos (tipos.py);
  * reportar errores con el número de línea del archivo;
  * conservar los nombres de columnas tal cual vienen.

Reglas del formato aceptado (documentadas como limitación):
  * una fila no puede tener más campos que el encabezado (error);
  * si tiene menos, los campos faltantes se rellenan con 'nada';
  * las comillas solo son especiales al inicio de un campo.
"""

from datos.fila import Fila
from datos.tabla import Tabla
from datos.tipos import NADA, texto_a_valor
from errores_base import ErrorArchivo, ErrorCSV


class LectorCSV:
    """Lector propio de archivos CSV para la instrucción 'monte'."""

    def __init__(self, separador=",", con_encabezado=True):
        if len(separador) != 1:
            raise ErrorCSV(
                "El separador debe ser un único carácter; llegué a recibir '{0}'.".format(
                    separador
                )
            )
        self.separador = separador
        self.con_encabezado = con_encabezado

    # ---------------------------------------------------------------- #

    def leer(self, ruta, nombre_tabla="tabla"):
        """Lee el archivo y devuelve una Tabla propia."""
        try:
            with open(ruta, "r", encoding="utf-8-sig", newline="") as manejador:
                contenido = manejador.read()
        except FileNotFoundError:
            raise ErrorArchivo(
                "No encontré el archivo '{0}'. Revisá la ruta relativa al "
                "directorio desde donde corres el programa.".format(ruta)
            )
        except OSError as problema:
            raise ErrorArchivo(
                "No pude leer el archivo '{0}': {1}.".format(ruta, problema)
            )
        except UnicodeDecodeError:
            raise ErrorArchivo(
                "El archivo '{0}' no está en UTF-8; guardalo con esa codificación.".format(ruta)
            )
        return self.leer_texto(contenido, nombre_tabla, ruta)

    def leer_texto(self, contenido, nombre_tabla="tabla", origen=""):
        """Lee el contenido CSV ya cargado en memoria (útil en pruebas)."""
        lineas = self._partir_lineas(contenido)
        if not lineas:
            raise ErrorCSV("El archivo CSV está vacío: no hay ni encabezados ni datos.")

        if self.con_encabezado:
            encabezado = self._partir_campos(lineas[0][1], lineas[0][0])
            nombres = [c if c != "" else "columna_{0}".format(i + 1)
                       for i, c in enumerate(encabezado)]
            crudas = [(n, self._partir_campos(l, n)) for n, l in lineas[1:]]
        else:
            todas = [self._partir_campos(l, n) for n, l in lineas]
            ancho = max(len(f) for f in todas)
            nombres = ["columna_{0}".format(i + 1) for i in range(ancho)]
            crudas = list(zip([n for n, _ in lineas], todas))

        filas = []
        for numero_linea, cruda in crudas:
            if len(cruda) > len(nombres):
                raise ErrorCSV(
                    "La línea {0} del CSV tiene {1} campos pero se esperaban {2}.".format(
                        numero_linea, len(cruda), len(nombres)
                    ),
                    linea_archivo=numero_linea,
                )
            valores = [texto_a_valor(campo) for campo in cruda]
            while len(valores) < len(nombres):
                valores.append(NADA)
            filas.append(Fila(valores))

        return Tabla(nombres, filas, nombre_tabla, origen or "texto en memoria")

    # ---------------------------------------------------------------- #
    # Separación de líneas
    # ---------------------------------------------------------------- #

    @staticmethod
    def _partir_lineas(contenido):
        """Divide en líneas numeradas, descartando las vacías.

        Acepta finales de línea \\n y \\r\\n. Una línea solo con espacios
        se considera vacía y se ignora.
        """
        lineas = []
        for numero, cruda in enumerate(contenido.split("\n"), 1):
            limpia = cruda.rstrip("\r")
            if limpia.strip() == "":
                continue
            lineas.append((numero, limpia))
        return lineas

    # ---------------------------------------------------------------- #
    # Separación de campos: máquina de estados carácter a carácter
    # ---------------------------------------------------------------- #

    def _partir_campos(self, linea, numero_linea):
        """Separa una línea en campos aplicando las reglas de comillas.

        Estados: FUERA (texto normal) y DENTRO (entre comillas dobles).
        En DENTRO, una comilla doble seguida de otra es una comilla
        literal (escape ""); una comilla sola cierra el campo.
        """
        campos = []
        actual = []
        dentro = False
        i = 0
        while i < len(linea):
            caracter = linea[i]
            if dentro:
                if caracter == '"':
                    if i + 1 < len(linea) and linea[i + 1] == '"':
                        actual.append('"')
                        i += 1
                    else:
                        dentro = False
                else:
                    actual.append(caracter)
            else:
                if caracter == '"' and not actual:
                    dentro = True
                elif caracter == self.separador:
                    campos.append("".join(actual))
                    actual = []
                else:
                    actual.append(caracter)
            i += 1

        if dentro:
            raise ErrorCSV(
                "Comillas sin cerrar en la línea {0} del CSV: el campo "
                "'{1}...' nunca se cierra.".format(numero_linea, "".join(actual)[:20]),
                linea_archivo=numero_linea,
                contexto=linea[:60],
            )
        campos.append("".join(actual))
        return campos
