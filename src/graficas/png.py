"""
AREPA - Escritor PNG propio (src/graficas/png.py)
-------------------------------------------------
Implementado por el equipo. Genera imágenes PNG RGB de 8 bits sin usar
bibliotecas externas: aquí viven el codificador DEFLATE (RFC 1951), la
envoltura de flujo comprimido (RFC 1950), el CRC-32 con tabla propia y
la suma Adler-32.

Qué hace:
  * arma la firma PNG y los chunks IHDR, IDAT e IEND con su CRC;
  * antepone el byte de filtro 0 (None) a cada fila de píxeles;
  * comprime con LZ77 + Huffman fijo (BTYPE=01) o con bloques guardados
    (BTYPE=00), ambos válidos según DEFLATE;
  * escribe el archivo creando los directorios que falten;
  * lee la cabecera IHDR de un PNG ya codificado.

Decisiones propias documentadas:
  * un único bloque DEFLATE final (BFINAL=1) para todo el flujo: el
    formato no impone límite de tamaño a un bloque de Huffman;
  * LZ77 voraz con hash exacto de 3 bytes (clave de 24 bits, sin
    colisiones) y cadena de posiciones anteriores limitada a 64
    candidatos, para que la codificación sea rápida en Python puro;
  * el modo "fijo" gana compresión y el modo "guardado" gana velocidad;
    el segundo se ofrece como alternativa verificable y depurable;
  * la comprobación de CRC al leer solo cubre la firma y el IHDR, que es
    lo mínimo para rechazar archivos ajenos.

Limitaciones:
  * solo profundidad 8, color RGB (tipo 2) y entrelazado 0;
  * no se implementan los filtros 1-4 ni bloques dinámicos (BTYPE=10);
  * la cadena de candidatos es acotada: en patrones muy ambiguos puede
    elegir un match algo más corto que el óptimo, nunca uno inválido.
"""

import os
import struct

# ---------------------------------------------------------------------- #
# Constantes del formato
# ---------------------------------------------------------------------- #

FIRMA = b"\x89PNG\r\n\x1a\n"

_PROFUNDIDAD = 8
_TIPO_COLOR_RGB = 2
_COMPRESION_PNG = 0
_FILTRO_PNG = 0
_INTERLACE_NINGUNO = 0

_TAMANO_VENTANA = 32768
_LARGO_MAXIMO = 258
_LARGO_MINIMO = 3
_MAXIMO_CANDIDATOS = 64
_TAMANO_BLOQUE_GUARDADO = 65535


# ---------------------------------------------------------------------- #
# CRC-32 (polinomio 0xEDB88320)
# ---------------------------------------------------------------------- #

def _construir_tabla_crc():
    """Tabla de 256 entradas para el CRC-32 estándar de PNG."""
    tabla = []
    for valor in range(256):
        resto = valor
        for _ in range(8):
            if resto & 1:
                resto = 0xEDB88320 ^ (resto >> 1)
            else:
                resto >>= 1
        tabla.append(resto)
    return tuple(tabla)


_TABLA_CRC = _construir_tabla_crc()


def crc32(datos):
    """CRC-32 de 'datos' con la tabla propia (mismo resultado que el estándar).

    Se usa para el CRC de cada chunk PNG, calculado sobre tipo + datos.
    """
    resto = 0xFFFFFFFF
    tabla = _TABLA_CRC
    for byte in datos:
        resto = tabla[(resto ^ byte) & 0xFF] ^ (resto >> 8)
    return resto ^ 0xFFFFFFFF


# ---------------------------------------------------------------------- #
# Adler-32 (módulo 65521)
# ---------------------------------------------------------------------- #

def adler32(datos):
    """Adler-32 de 'datos', la suma de control del flujo RFC 1950."""
    a = 1
    b = 0
    total = len(datos)
    inicio = 0
    # Se procesan bloques de 5552 bytes: es el mayor tamaño para el que
    # 'b' no desborda antes de reducir el módulo.
    while inicio < total:
        fin = inicio + 5552
        if fin > total:
            fin = total
        for byte in datos[inicio:fin]:
            a += byte
            b += a
        a %= 65521
        b %= 65521
        inicio = fin
    return (b << 16) | a


# ---------------------------------------------------------------------- #
# Escritor de bits LSB-first
# ---------------------------------------------------------------------- #

class _EscritorBits:
    """Acumula bits en orden LSB-first, como exige DEFLATE."""

    __slots__ = ("_bytes", "_acumulado", "_bits")

    def __init__(self):
        self._bytes = bytearray()
        self._acumulado = 0
        self._bits = 0

    def escribir(self, valor, cantidad):
        """Escribe los 'cantidad' bits menos significativos de 'valor'."""
        if cantidad < 0:
            raise ValueError("la cantidad de bits no puede ser negativa")
        self._acumulado |= (valor & ((1 << cantidad) - 1)) << self._bits
        self._bits += cantidad
        while self._bits >= 8:
            self._bytes.append(self._acumulado & 0xFF)
            self._acumulado >>= 8
            self._bits -= 8

    def escribir_codigo(self, codigo, cantidad):
        """Escribe un código Huffman: los códigos van MSB-first.

        DEFLATE llena el flujo desde el bit menos significativo del byte,
        pero los códigos Huffman se definen de izquierda a derecha, así
        que hay que invertirlos antes de volcarlos.
        """
        invertido = 0
        for _ in range(cantidad):
            invertido = (invertido << 1) | (codigo & 1)
            codigo >>= 1
        self.escribir(invertido, cantidad)

    def alinear(self):
        """Rellena con ceros hasta el siguiente límite de byte."""
        if self._bits:
            self.escribir(0, 8 - self._bits)

    def escribir_bytes(self, datos):
        """Añade bytes crudos; exige que el flujo esté alineado."""
        if self._bits:
            raise ValueError("el flujo debe estar alineado para escribir bytes")
        self._bytes.extend(datos)

    def terminar(self):
        """Cierra el flujo rellenando el último byte con ceros."""
        self.alinear()
        return bytes(self._bytes)


# ---------------------------------------------------------------------- #
# Tablas fijas de Huffman (RFC 1951, sección 3.2.6)
# ---------------------------------------------------------------------- #

def _invertir(codigo, cantidad):
    """Devuelve 'codigo' con sus 'cantidad' bits en orden inverso."""
    invertido = 0
    for _ in range(cantidad):
        invertido = (invertido << 1) | (codigo & 1)
        codigo >>= 1
    return invertido


def _construir_tabla_fija():
    """Tabla (código invertido, bits) para los 288 símbolos fijos."""
    tabla = []
    for simbolo in range(288):
        if simbolo <= 143:
            codigo, bits = 0x30 + simbolo, 8
        elif simbolo <= 255:
            codigo, bits = 0x190 + (simbolo - 144), 9
        elif simbolo <= 279:
            codigo, bits = simbolo - 256, 7
        else:
            codigo, bits = 0xC0 + (simbolo - 280), 8
        tabla.append((_invertir(codigo, bits), bits))
    return tuple(tabla)


_TABLA_FIJA = _construir_tabla_fija()

# Longitudes 3..258: base del rango y bits extra, códigos 257..285.
_BASES_LONGITUD = (
    3, 4, 5, 6, 7, 8, 9, 10,
    11, 13, 15, 17,
    19, 23, 27, 31,
    35, 43, 51, 59,
    67, 83, 99, 115,
    131, 163, 195, 227,
    258,
)
_BITS_EXTRA_LONGITUD = (
    0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1,
    2, 2, 2, 2,
    3, 3, 3, 3,
    4, 4, 4, 4,
    5, 5, 5, 5,
    0,
)

# Distancias 1..32768: base del rango y bits extra, códigos 0..29 (5 bits).
_BASES_DISTANCIA = (
    1, 2, 3, 4,
    5, 7,
    9, 13,
    17, 25,
    33, 49,
    65, 97,
    129, 193,
    257, 385,
    513, 769,
    1025, 1537,
    2049, 3073,
    4097, 6145,
    8193, 12289,
    16385, 24577,
)
_BITS_EXTRA_DISTANCIA = (
    0, 0, 0, 0,
    1, 1,
    2, 2,
    3, 3,
    4, 4,
    5, 5,
    6, 6,
    7, 7,
    8, 8,
    9, 9,
    10, 10,
    11, 11,
    12, 12,
    13, 13,
)


def _emitir_simbolo(escritor, simbolo):
    """Emite un símbolo literal/longitud con su código fijo."""
    codigo, bits = _TABLA_FIJA[simbolo]
    escritor.escribir(codigo, bits)


def _emitir_longitud(escritor, largo):
    """Emite el par código de longitud + bits extra para 'largo'."""
    if largo < _LARGO_MINIMO or largo > _LARGO_MAXIMO:
        raise ValueError(
            "la longitud {0} está fuera del rango permitido ({1}..{2}).".format(
                largo, _LARGO_MINIMO, _LARGO_MAXIMO
            )
        )
    indice = 0
    for posicion, base in enumerate(_BASES_LONGITUD):
        if base > largo:
            break
        indice = posicion
    _emitir_simbolo(escritor, 257 + indice)
    extra = _BITS_EXTRA_LONGITUD[indice]
    if extra:
        escritor.escribir(largo - _BASES_LONGITUD[indice], extra)


def _emitir_distancia(escritor, distancia):
    """Emite el código de distancia (5 bits) y sus bits extra."""
    if distancia < 1 or distancia > _TAMANO_VENTANA:
        raise ValueError(
            "la distancia {0} está fuera del rango permitido (1..{1}).".format(
                distancia, _TAMANO_VENTANA
            )
        )
    indice = 0
    for posicion, base in enumerate(_BASES_DISTANCIA):
        if base > distancia:
            break
        indice = posicion
    escritor.escribir_codigo(indice, 5)
    extra = _BITS_EXTRA_DISTANCIA[indice]
    if extra:
        escritor.escribir(distancia - _BASES_DISTANCIA[indice], extra)


# ---------------------------------------------------------------------- #
# LZ77 voraz con cadena de posiciones
# ---------------------------------------------------------------------- #

def _largo_coincidencia(datos, inicio_a, inicio_b, maximo):
    """Cuenta bytes iguales desde dos posiciones, hasta 'maximo'.

    Se comparan trozos de 16 bytes para que el bucle de Python haga
    muchas menos iteraciones que comparando byte a byte.
    """
    largo = 0
    while (
        largo + 16 <= maximo
        and datos[inicio_a + largo:inicio_a + largo + 16]
        == datos[inicio_b + largo:inicio_b + largo + 16]
    ):
        largo += 16
    while largo < maximo and datos[inicio_a + largo] == datos[inicio_b + largo]:
        largo += 1
    return largo


class _BuscadorLz77:
    """Encuentra coincidencias previas dentro de la ventana deslizante."""

    __slots__ = ("_datos", "_cadenas")

    def __init__(self, datos):
        self._datos = datos
        # clave de 3 bytes exactos -> posiciones crecientes donde aparece
        self._cadenas = {}

    def _clave(self, posicion):
        """Clave de 24 bits con los tres bytes que empiezan en 'posicion'."""
        datos = self._datos
        return (datos[posicion] << 16) | (datos[posicion + 1] << 8) | datos[posicion + 2]

    def registrar(self, posicion):
        """Anota 'posicion' como candidata para futuras búsquedas."""
        if posicion + 3 > len(self._datos):
            return
        clave = self._clave(posicion)
        cadena = self._cadenas.get(clave)
        if cadena is None:
            self._cadenas[clave] = [posicion]
            return
        cadena.append(posicion)
        # Se conservan solo las posiciones recientes: la ventana útil es
        # de 32768 bytes y una cadena enorme solo gastaría memoria.
        if len(cadena) > 128:
            del cadena[:64]

    def buscar(self, posicion):
        """Devuelve (largo, distancia) del mejor match, o (0, 0)."""
        datos = self._datos
        if posicion + _LARGO_MINIMO > len(datos):
            return 0, 0
        cadena = self._cadenas.get(self._clave(posicion))
        if not cadena:
            return 0, 0

        tope = len(datos) - posicion
        if tope > _LARGO_MAXIMO:
            tope = _LARGO_MAXIMO
        limite = posicion - _TAMANO_VENTANA
        mejor_largo = _LARGO_MINIMO - 1
        mejor_distancia = 0
        revisados = 0
        for candidata in reversed(cadena):
            if candidata < limite:
                break
            revisados += 1
            if revisados > _MAXIMO_CANDIDATOS:
                break
            # La cadena garantiza que los 3 primeros bytes coinciden.
            largo = _LARGO_MINIMO + _largo_coincidencia(
                datos, candidata + _LARGO_MINIMO, posicion + _LARGO_MINIMO, tope - _LARGO_MINIMO
            )
            if largo > mejor_largo:
                mejor_largo = largo
                mejor_distancia = posicion - candidata
                if largo >= tope:
                    break
        if mejor_largo >= _LARGO_MINIMO:
            return mejor_largo, mejor_distancia
        return 0, 0


# ---------------------------------------------------------------------- #
# Compresión DEFLATE
# ---------------------------------------------------------------------- #

def _comprimir_fijo(datos):
    """Un bloque final BTYPE=01 con LZ77 + códigos Huffman fijos."""
    escritor = _EscritorBits()
    escritor.escribir(1, 1)  # BFINAL = 1
    escritor.escribir(1, 2)  # BTYPE = 01 (Huffman fijo)

    buscador = _BuscadorLz77(datos)
    total = len(datos)
    posicion = 0
    while posicion < total:
        largo, distancia = buscador.buscar(posicion)
        if largo >= _LARGO_MINIMO:
            _emitir_longitud(escritor, largo)
            _emitir_distancia(escritor, distancia)
            for desplazamiento in range(largo):
                buscador.registrar(posicion + desplazamiento)
            posicion += largo
        else:
            _emitir_simbolo(escritor, datos[posicion])
            buscador.registrar(posicion)
            posicion += 1

    _emitir_simbolo(escritor, 256)  # fin de bloque
    return escritor.terminar()


def _comprimir_guardado(datos):
    """Bloques BTYPE=00 (stored): sin compresión, solo empaquetado."""
    escritor = _EscritorBits()
    total = len(datos)
    if total == 0:
        escritor.escribir(1, 1)  # BFINAL = 1
        escritor.escribir(0, 2)  # BTYPE = 00
        escritor.alinear()
        escritor.escribir_bytes(struct.pack("<HH", 0, 0xFFFF))
        return escritor.terminar()

    inicio = 0
    while inicio < total:
        fin = inicio + _TAMANO_BLOQUE_GUARDADO
        if fin > total:
            fin = total
        trozo = datos[inicio:fin]
        es_ultimo = fin >= total
        escritor.escribir(1 if es_ultimo else 0, 1)
        escritor.escribir(0, 2)
        escritor.alinear()
        escritor.escribir_bytes(
            struct.pack("<HH", len(trozo), len(trozo) ^ 0xFFFF)
        )
        escritor.escribir_bytes(trozo)
        inicio = fin
    return escritor.terminar()


def _envolver_deflate(comprimido, original):
    """Envoltura de flujo comprimido de RFC 1950 con Adler-32 final."""
    return b"\x78\x01" + comprimido + struct.pack(">I", adler32(original))


# ---------------------------------------------------------------------- #
# Chunks PNG
# ---------------------------------------------------------------------- #

def _chunk(tipo, datos):
    """Arma un chunk PNG: longitud, tipo, datos y CRC-32 de tipo + datos."""
    if len(tipo) != 4:
        raise ValueError("el tipo de chunk debe medir 4 bytes ASCII.")
    return (
        struct.pack(">I", len(datos))
        + tipo
        + datos
        + struct.pack(">I", crc32(tipo + datos))
    )


def _validar_entero_positivo(valor, nombre):
    """Exige un entero (sin bool) mayor que cero."""
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ValueError(
            "'{0}' debe ser un número entero; recibí {1}.".format(nombre, repr(valor))
        )
    if valor <= 0:
        raise ValueError(
            "'{0}' debe ser mayor que cero; recibí {1}.".format(nombre, valor)
        )


def _normalizar_pixeles(pixeles, esperado):
    """Valida el búfer RGB y lo devuelve como bytes inmutables."""
    if not isinstance(pixeles, (bytes, bytearray)):
        raise ValueError(
            "'pixeles' debe ser bytes o bytearray RGB; recibí {0}.".format(
                type(pixeles).__name__
            )
        )
    if len(pixeles) != esperado:
        raise ValueError(
            "el tamaño de 'pixeles' es incorrecto: se esperaban {0} bytes "
            "(ancho * alto * 3) y llegaron {1}.".format(esperado, len(pixeles))
        )
    return bytes(pixeles)


def _normalizar_compresion(compresion):
    """Valida el modo de compresión y devuelve su nombre canónico."""
    if compresion not in ("fijo", "guardado"):
        raise ValueError(
            "compresión desconocida {0}: use 'fijo' o 'guardado'.".format(
                repr(compresion)
            )
        )
    return compresion


def _armar_scanlines(ancho, alto, pixeles):
    """Antepone el filtro 0 (None) a cada fila de píxeles RGB."""
    paso = ancho * 3
    crudo = bytearray(alto * (paso + 1))
    for fila in range(alto):
        destino = fila * (paso + 1)
        crudo[destino] = _FILTRO_PNG
        origen = fila * paso
        crudo[destino + 1:destino + 1 + paso] = pixeles[origen:origen + paso]
    return bytes(crudo)


# ---------------------------------------------------------------------- #
# API pública
# ---------------------------------------------------------------------- #

def codificar_png(ancho, alto, pixeles, compresion="fijo"):
    """Codifica una imagen RGB de 8 bits y devuelve los bytes del PNG.

    'pixeles' debe traer exactamente ancho * alto * 3 bytes en orden de
    filas. 'compresion' admite "fijo" (Huffman fijo + LZ77, por defecto)
    o "guardado" (bloques sin comprimir). Cualquier dato inválido lanza
    ValueError con un mensaje explicativo.
    """
    _validar_entero_positivo(ancho, "ancho")
    _validar_entero_positivo(alto, "alto")
    modo = _normalizar_compresion(compresion)
    pixeles = _normalizar_pixeles(pixeles, ancho * alto * 3)

    crudo = _armar_scanlines(ancho, alto, pixeles)
    if modo == "fijo":
        comprimido = _comprimir_fijo(crudo)
    else:
        comprimido = _comprimir_guardado(crudo)
    flujo = _envolver_deflate(comprimido, crudo)

    ihdr = struct.pack(
        ">IIBBBBB",
        ancho,
        alto,
        _PROFUNDIDAD,
        _TIPO_COLOR_RGB,
        _COMPRESION_PNG,
        _FILTRO_PNG,
        _INTERLACE_NINGUNO,
    )
    return (
        FIRMA
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", flujo)
        + _chunk(b"IEND", b"")
    )


def escribir_png(ruta, ancho, alto, pixeles, compresion="fijo"):
    """Codifica la imagen y la guarda en 'ruta'; devuelve los bytes escritos.

    Crea los directorios padres que falten. El contenido es idéntico al
    que devolvería codificar_png con los mismos argumentos.
    """
    datos = codificar_png(ancho, alto, pixeles, compresion)
    destino = os.fspath(ruta)
    carpeta = os.path.dirname(os.path.abspath(destino))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta, exist_ok=True)
    with open(destino, "wb") as archivo:
        archivo.write(datos)
    return len(datos)


def leer_cabecera(datos):
    """Lee el IHDR de un PNG y devuelve sus campos principales.

    El diccionario resultante tiene las claves "ancho", "alto",
    "profundidad", "tipo_color" e "interlace". Lanza ValueError si la
    firma o el IHDR no son válidos.
    """
    if not isinstance(datos, (bytes, bytearray)):
        raise ValueError(
            "'datos' debe ser bytes o bytearray; recibí {0}.".format(
                type(datos).__name__
            )
        )
    if len(datos) < 8 + 12 + 13:
        raise ValueError("el archivo es demasiado corto para ser un PNG.")
    if datos[:8] != FIRMA:
        raise ValueError("la firma no corresponde a un PNG válido.")

    longitud = struct.unpack(">I", datos[8:12])[0]
    tipo = datos[12:16]
    if tipo != b"IHDR" or longitud != 13:
        raise ValueError("el primer chunk debe ser un IHDR de 13 bytes.")
    if len(datos) < 8 + 12 + 13:
        raise ValueError("el IHDR está incompleto.")

    (
        ancho,
        alto,
        profundidad,
        tipo_color,
        compresion,
        filtro,
        interlace,
    ) = struct.unpack(">IIBBBBB", datos[16:29])
    if ancho <= 0 or alto <= 0:
        raise ValueError("el IHDR declara un tamaño inválido.")
    if compresion != _COMPRESION_PNG or filtro != _FILTRO_PNG:
        raise ValueError("el IHDR usa un método de compresión o filtro no soportado.")
    return {
        "ancho": ancho,
        "alto": alto,
        "profundidad": profundidad,
        "tipo_color": tipo_color,
        "interlace": interlace,
    }
