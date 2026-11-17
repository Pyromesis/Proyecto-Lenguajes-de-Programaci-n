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
        except ValueError:
            raise ErrorArchivo(
                "La ruta CSV '{0}' no es válida; revisá sus caracteres.".format(ruta)
            ) from None
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
            if len(set(nombres)) != len(nombres):
                raise ErrorCSV("El encabezado CSV tiene nombres de columna repetidos; "
                               "cada columna debe tener un nombre único.",
                               linea_archivo=lineas[0][0])
            crudas = [(n, self._partir_campos(l, n, con_marcas=True)) for n, l in lineas[1:]]
        else:
            todas = [self._partir_campos(l, n, con_marcas=True) for n, l in lineas]
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
            # Las comillas son una declaración explícita de texto, no solo
            # protección del separador. Esto hace reversible el escritor.
            valores = [campo if citado else (NADA if campo.strip() == "nada"
                       else texto_a_valor(campo)) for campo, citado in cruda]
            while len(valores) < len(nombres):
                valores.append(NADA)
            filas.append(Fila(valores))

        return Tabla(nombres, filas, nombre_tabla, origen or "texto en memoria")

    # ---------------------------------------------------------------- #
    # Separación de líneas
    # ---------------------------------------------------------------- #

    def _partir_lineas(self, contenido):
        """Separa registros conservando saltos dentro de campos entre comillas.

        Cada registro conserva el número de su primera línea física para los
        diagnósticos. Las reglas de apertura y escape coinciden con las de
        _partir_campos; una comilla en medio de texto no abre un campo.
        """
        lineas = []
        inicio = 0
        numero = primera = 1
        dentro = False
        inicio_campo = True
        i = 0
        while i < len(contenido):
            caracter = contenido[i]
            if dentro:
                if caracter == '"':
                    if i + 1 < len(contenido) and contenido[i + 1] == '"':
                        i += 2
                        continue
                    dentro = False
            elif caracter == "\n":
                registro = contenido[inicio:i].rstrip("\r")
                if registro.strip():
                    lineas.append((primera, registro))
                inicio = i + 1
                primera = numero + 1
                inicio_campo = True
            elif caracter == self.separador:
                inicio_campo = True
            elif caracter == '"' and inicio_campo:
                dentro = True
                inicio_campo = False
            else:
                inicio_campo = False
            if caracter == "\n":
                numero += 1
            i += 1
        registro = contenido[inicio:].rstrip("\r")
        if registro.strip():
            lineas.append((primera, registro))
        return lineas

    # ---------------------------------------------------------------- #
    # Separación de campos: máquina de estados carácter a carácter
    # ---------------------------------------------------------------- #

    def _partir_campos(self, linea, numero_linea, con_marcas=False):
        """Separa una línea en campos aplicando las reglas de comillas.

        Estados: FUERA (texto normal) y DENTRO (entre comillas dobles).
        En DENTRO, una comilla doble seguida de otra es una comilla
        literal (escape ""); una comilla sola cierra el campo.
        """
        campos = []
        actual = []
        dentro = False
        citado = cerrado = False
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
                        cerrado = True
                else:
                    actual.append(caracter)
            else:
                if cerrado and caracter != self.separador:
                    if caracter not in (" ", "\t"):
                        raise ErrorCSV("Hay texto después del cierre de comillas "
                                       "en la línea {0} del CSV; falta un separador.".format(numero_linea),
                                       linea_archivo=numero_linea, contexto=linea[:60])
                elif caracter == '"' and not actual:
                    dentro = True
                    citado = True
                elif caracter == self.separador:
                    valor = "".join(actual)
                    campos.append((valor, citado) if con_marcas else valor)
                    actual = []
                    citado = cerrado = False
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
        valor = "".join(actual)
        campos.append((valor, citado) if con_marcas else valor)
        return campos
