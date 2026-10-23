"""
AREPA - Acceso indexado propio (src/datos/acceso.py)
----------------------------------------------------
Funciones reutilizables por el evaluador de expresiones y por el
ejecutor para leer y escribir dentro de Lista, Registro, Tabla y Fila.

La semántica pública del lenguaje cuenta desde 1: 'nums[1]' es el
primer elemento y 'gente[1]' es la primera fila. Las estructuras
internas siguen siendo 0-based; aquí se hace la traducción y se
validan los rangos con mensajes en español.

Qué hace:
  * obtener():  contenedor + índice -> valor (o Registro de fila);
  * asignar():  contenedor + índice + valor -> actualiza el contenedor;
  * valores_para_fila(): normaliza una Lista/Registro a los valores de
    una fila de Tabla, respetando el orden de sus columnas.

Decisiones propias documentadas:
  * acceder a una fila de Tabla devuelve un Registro enlazado a la
    tabla (Tabla.fila_como_registro), así que asignar sobre él también
    actualiza la celda real;
  * en un Registro el índice debe ser texto (la clave); en Lista, Tabla
    y Fila debe ser un entero (nunca un lógico);
  * un índice fuera de rango es ErrorOperacion e informa el tamaño con
    numeración 1-based;
  * una clave inexistente es ErrorColumna (la produce Registro.obtener
    y aquí solo se completa su línea/columna).

Limitaciones:
  * no hay índices negativos ni acceso por rebanadas (slices);
  * no se valida la duplicación de columnas al construir una Tabla con
    'arme' (esa validación corresponde a Tabla).
"""

from datos.fila import Fila
from datos.lista import Lista
from datos.registro import Registro
from datos.tabla import Tabla
from datos.tipos import nombre_tipo
from errores_base import ErrorColumna, ErrorOperacion, ErrorTipos


def obtener(contenedor, indice, linea=-1, columna=-1):
    """Devuelve el valor de 'contenedor' en 'indice' (1-based).

    * Lista y Fila: índice entero 1..N;
    * Tabla: fila entera 1..N como Registro enlazado a la tabla;
    * Registro: clave de texto.
    """
    if isinstance(contenedor, Tabla):
        posicion = _exigir_entero(
            indice, "la tabla '{0}'".format(contenedor.nombre), linea, columna
        )
        _validar_rango(
            posicion, contenedor.num_filas, "fila", "La tabla '{0}'".format(
                contenedor.nombre
            ), linea, columna,
        )
        return contenedor.fila_como_registro(posicion - 1)

    if isinstance(contenedor, Lista):
        posicion = _exigir_entero(indice, "la lista", linea, columna)
        _validar_rango(
            posicion, contenedor.largo(), "elemento", "La lista", linea, columna
        )
        return contenedor.obtener(posicion - 1)

    if isinstance(contenedor, Registro):
        if not isinstance(indice, str):
            raise ErrorTipos(
                "Para acceder a un registro la clave debe ser texto, pero "
                "llegó un valor de tipo {0}.".format(nombre_tipo(indice)),
                linea=linea,
                columna=columna,
            )
        try:
            return contenedor.obtener(indice)
        except ErrorColumna as problema:
            _completar_ubicacion(problema, linea, columna)
            raise

    if isinstance(contenedor, Fila):
        posicion = _exigir_entero(indice, "la fila", linea, columna)
        _validar_rango(
            posicion, len(contenedor.valores), "elemento", "La fila",
            linea, columna,
        )
        return contenedor.valor_en(posicion - 1)

    raise ErrorTipos(
        "No se puede acceder con índices a un valor de tipo {0}.".format(
            nombre_tipo(contenedor)
        ),
        linea=linea,
        columna=columna,
    )


def asignar(contenedor, indice, valor, linea=-1, columna=-1):
    """Actualiza 'contenedor[indice]' con 'valor' (índice 1-based).

    En Tabla, 'valor' debe ser una Lista (valores por posición) o un
    Registro (valores por nombre de columna). Devuelve el valor.
    """
    if isinstance(contenedor, Lista):
        posicion = _exigir_entero(indice, "la lista", linea, columna)
        _validar_rango(
            posicion, contenedor.largo(), "elemento", "La lista", linea, columna
        )
        contenedor.poner(posicion - 1, valor)
        return valor

    if isinstance(contenedor, Registro):
        if not isinstance(indice, str):
            raise ErrorTipos(
                "Para asignar en un registro la clave debe ser texto, pero "
                "llegó un valor de tipo {0}.".format(nombre_tipo(indice)),
                linea=linea,
                columna=columna,
            )
        try:
            contenedor.poner(indice, valor)
        except ErrorColumna as problema:
            _completar_ubicacion(problema, linea, columna)
            raise
        return valor

    if isinstance(contenedor, Tabla):
        posicion = _exigir_entero(
            indice, "la tabla '{0}'".format(contenedor.nombre), linea, columna
        )
        _validar_rango(
            posicion, contenedor.num_filas, "fila", "La tabla '{0}'".format(
                contenedor.nombre
            ), linea, columna,
        )
        contenedor.poner_fila(
            posicion - 1,
            valores_para_fila(contenedor, valor, linea, columna),
        )
        return valor

    if isinstance(contenedor, Fila):
        posicion = _exigir_entero(indice, "la fila", linea, columna)
        _validar_rango(
            posicion, len(contenedor.valores), "elemento", "La fila",
            linea, columna,
        )
        contenedor.poner_en(posicion - 1, valor)
        return valor

    raise ErrorTipos(
        "No se puede asignar con índices en un valor de tipo {0}.".format(
            nombre_tipo(contenedor)
        ),
        linea=linea,
        columna=columna,
    )


def valores_para_fila(tabla, valor, linea=-1, columna=-1):
    """Normaliza 'valor' a la lista de valores de una fila de 'tabla'.

    Acepta una Lista (por posición), una Fila o un Registro (por nombre
    de columna). Lanza ErrorColumna si al Registro le falta una columna
    de la tabla y ErrorTipos si el largo posicional no coincide.
    """
    if isinstance(valor, Registro):
        valores = []
        for nombre in tabla.nombres_columnas:
            if not valor.tiene(nombre):
                raise ErrorColumna(
                    "El registro no trae la columna '{0}' de la tabla '{1}'. "
                    "Claves del registro: {2}.".format(
                        nombre, tabla.nombre, ", ".join(valor.claves()) or "(ninguna)"
                    ),
                    linea=linea,
                    columna=columna,
                )
            valores.append(valor.obtener(nombre))
        return valores

    if isinstance(valor, Lista):
        valores = list(valor)
    elif isinstance(valor, Fila):
        valores = list(valor.valores)
    else:
        raise ErrorTipos(
            "Para una fila de la tabla '{0}' se necesita una lista o un "
            "registro, pero llegó un valor de tipo {1}.".format(
                tabla.nombre, nombre_tipo(valor)
            ),
            linea=linea,
            columna=columna,
        )

    if len(valores) != tabla.num_columnas:
        raise ErrorTipos(
            "La fila trae {0} {1} pero la tabla '{2}' tiene {3} columnas.".format(
                len(valores),
                "valor" if len(valores) == 1 else "valores",
                tabla.nombre,
                tabla.num_columnas,
            ),
            linea=linea,
            columna=columna,
        )
    return valores


# ---------------------------------------------------------------------- #
# Utilidades internas de validación
# ---------------------------------------------------------------------- #

def _exigir_entero(indice, sujeto, linea, columna):
    """Devuelve el índice si es entero (bool no cuenta); si no, ErrorTipos."""
    if not isinstance(indice, int) or isinstance(indice, bool):
        raise ErrorTipos(
            "El índice para {0} debe ser un número entero, pero llegó un "
            "valor de tipo {1}.".format(sujeto, nombre_tipo(indice)),
            linea=linea,
            columna=columna,
        )
    return indice


def _validar_rango(posicion, total, unidad, sujeto, linea, columna):
    """Valida 1 <= posicion <= total; ErrorOperacion con tamaño 1-based."""
    if posicion < 1 or posicion > total:
        raise ErrorOperacion(
            "{0} tiene {1} {2}s; no existe {3} {4} (se cuenta desde 1).".format(
                sujeto, total, unidad, _articulo(unidad), posicion
            ),
            linea=linea,
            columna=columna,
        )


def _articulo(unidad):
    return "la" if unidad == "fila" else "el"


def _completar_ubicacion(problema, linea, columna):
    """Completa línea/columna de un error propio si aún no las tiene."""
    if problema.linea == -1 and linea != -1:
        problema.linea = linea
    if problema.columna == -1 and columna != -1:
        problema.columna = columna
