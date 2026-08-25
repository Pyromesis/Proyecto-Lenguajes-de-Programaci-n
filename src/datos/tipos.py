"""
AREPA - Sistema propio de tipos de valores (src/datos/tipos.py)
---------------------------------------------------------------
Implementado por el equipo. Clasifica y convierte los valores del DSL
sin usar ninguna biblioteca externa: solo operaciones básicas de Python.

Valores del lenguaje:
  * numero  -> int / float de Python (elegidos como representación)
  * texto   -> str
  * logico  -> bool (solo los literales 'obvio' y 'falso')
  * nada    -> ValorNulo (singleton propio, equivalente a un faltante)

Qué hace:
  * detectar el tipo de un valor;
  * convertir texto del CSV a valor del lenguaje;
  * convertir un valor a un tipo declarado (convierta col -> tipo);
  * validar fechas en formato AAAA-MM-DD con calendario propio.

Limitaciones:
  * las fechas se guardan como texto validado, no como objeto de fecha;
  * los decimales usan la aritmética binaria de Python (sin decimal fijo).
"""

from errores_base import ErrorTipos


class ValorNulo:
    """Representa el literal 'nada' (valor faltante) del DSL."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __repr__(self):
        return "nada"

    def __eq__(self, otro):
        return isinstance(otro, ValorNulo)

    def __hash__(self):
        return hash("nada")


NADA = ValorNulo()

TIPOS = ("numero", "texto", "logico", "fecha")


def es_nada(valor):
    return isinstance(valor, ValorNulo)


def es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def es_texto(valor):
    return isinstance(valor, str)


def es_logico(valor):
    return isinstance(valor, bool)


def nombre_tipo(valor):
    """Devuelve el nombre del tipo del valor según el vocabulario del DSL."""
    if es_nada(valor):
        return "nada"
    if es_logico(valor):
        return "logico"
    if es_numero(valor):
        return "numero"
    if es_texto(valor):
        return "texto"
    return type(valor).__name__


def texto_a_valor(texto):
    """Convierte un campo crudo del CSV al valor del lenguaje más ajustado.

    Orden de intento: entero, decimal, lógico, texto. Si nada encaja, el
    campo permanece como texto (nunca se lanza error aquí).
    """
    limpio = texto.strip()
    if limpio == "":
        return NADA
    try:
        return int(limpio)
    except ValueError:
        pass
    try:
        return float(limpio)
    except ValueError:
        pass
    if limpio == "obvio":
        return True
    if limpio == "falso":
        return False
    return limpio


def convertir_a_tipo(valor, tipo, contexto=""):
    """Convierte un valor al tipo declarado en 'convierta col -> tipo'.

    Lanza ErrorTipos con un mensaje comprensible si la conversión no es
    posible (por ejemplo texto 'abc' a numero).
    """
    if tipo not in TIPOS:
        raise ErrorTipos(
            "El tipo '{0}' no existe; los tipos válidos son: {1}.".format(
                tipo, ", ".join(TIPOS)
            ),
            contexto=contexto,
        )
    if es_nada(valor):
        return NADA

    if tipo == "texto":
        if es_texto(valor):
            return valor
        if es_logico(valor):
            return "obvio" if valor else "falso"
        return _numero_a_texto(valor)

    if tipo == "numero":
        if es_numero(valor):
            return valor
        if es_texto(valor):
            try:
                return int(valor.strip())
            except ValueError:
                try:
                    return float(valor.strip())
                except ValueError:
                    raise ErrorTipos(
                        "No pude convertir '{0}' a numero{1}.".format(valor, _donde(contexto)),
                        contexto=contexto,
                    )
        raise ErrorTipos(
            "No puedo convertir un valor {0} a numero{1}.".format(
                nombre_tipo(valor), _donde(contexto)
            ),
            contexto=contexto,
        )

    if tipo == "logico":
        if es_logico(valor):
            return valor
        if es_texto(valor) and valor.strip() in ("obvio", "falso"):
            return valor.strip() == "obvio"
        raise ErrorTipos(
            "No puedo convertir '{0}' a logico{1}; solo 'obvio' y 'falso'.".format(
                valor, _donde(contexto)
            ),
            contexto=contexto,
        )

    # tipo == "fecha": se acepta únicamente el formato AAAA-MM-DD
    if es_texto(valor) and _es_fecha_valida(valor.strip()):
        return valor.strip()
    raise ErrorTipos(
        "'{0}' no es una fecha válida{1}; se espera el formato AAAA-MM-DD.".format(
            valor, _donde(contexto)
        ),
        contexto=contexto,
    )


def _numero_a_texto(numero):
    """Formatea números sin el '.0' de los enteros guardados como float."""
    if isinstance(numero, float) and numero.is_integer():
        return str(int(numero))
    return str(numero)


def _donde(contexto):
    return " ({0})".format(contexto) if contexto else ""


def _es_fecha_valida(texto):
    """Validación propia de fechas AAAA-MM-DD (años bisiestos incluidos)."""
    if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
        return False
    parte_anio, parte_mes, parte_dia = texto[:4], texto[5:7], texto[8:10]
    if not (parte_anio.isdigit() and parte_mes.isdigit() and parte_dia.isdigit()):
        return False
    anio, mes, dia = int(parte_anio), int(parte_mes), int(parte_dia)
    if anio < 1 or mes < 1 or mes > 12 or dia < 1:
        return False
    dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if mes == 2 and _es_bisiesto(anio):
        dias_mes[1] = 29
    return dia <= dias_mes[mes - 1]


def _es_bisiesto(anio):
    return (anio % 4 == 0 and anio % 100 != 0) or anio % 400 == 0


def inferir_tipo(valores):
    """Infiere el tipo dominante de una columna a partir de sus valores.

    Ignora los 'nada'. Si hay mezcla de enteros y decimales devuelve
    'numero'; si no hay valores devuelve 'texto'.
    """
    presentes = [v for v in valores if not es_nada(v)]
    if not presentes:
        return "texto"
    if all(es_logico(v) for v in presentes):
        return "logico"
    if all(es_numero(v) for v in presentes):
        return "numero"
    if all(es_texto(v) for v in presentes) and all(_es_fecha_valida(v) for v in presentes):
        return "fecha"
    return "texto"
