"""
AREPA - Pruebas del escritor PNG propio y del motor de gráficas
--------------------------------------------------------------
Verifica el codificador de src/graficas/png.py con comprobaciones
independientes: el flujo comprimido se descomprime con la biblioteca
estándar (solo en las pruebas) y el CRC de cada chunk se recalcula con
una implementación ajena al codificador.

También cubre la fuente bitmap, el lienzo, las escalas y los cinco
tipos de gráfica (barras, líneas, histograma, dispersión y cajas).

Cubre:
  * firma, orden de chunks e IHDR/IEND;
  * vectores conocidos de CRC-32 y Adler-32;
  * lectura de cabecera y rechazo de firmas ajenas;
  * ida y vuelta de las scanlines en modo "fijo" y "guardado";
  * compresión de imágenes sólidas, patrones, gradientes y 400x300;
  * validaciones de tamaño, dimensiones, tipo de búfer y compresión;
  * escritura en disco con creación de directorios;
  * glifos ASCII, normalización de tildes y medidas de texto;
  * primitivas del lienzo, escalas y estadística de las gráficas.

Uso:
    python3 pruebas/test_graficas.py
"""

import binascii
import csv
import hashlib
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from graficas.png import (  # noqa: E402
    FIRMA,
    adler32,
    codificar_png,
    crc32,
    escribir_png,
    leer_cabecera,
)

from graficas.escalas import (  # noqa: E402
    EscalaBanda,
    EscalaLineal,
    formatear,
)
from graficas.fuente import (  # noqa: E402
    GLIFOS,
    alto_texto,
    ancho_texto,
    filas,
    normalizar_texto,
)
from graficas.lienzo import Lienzo  # noqa: E402
from graficas.tipos_grafica import (  # noqa: E402
    PALETA,
    TIPOS,
    Grafica,
    Serie,
    _acortar_etiqueta,
    _seleccionar_etiquetas,
    cuartiles,
    cubetas_histograma,
    dibujar,
)

from errores_base import ErrorColumna, ErrorGrafica  # noqa: E402
from lenguaje.analizador import analizar  # noqa: E402
from runtime.ejecutor import EjecutorArepa  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


# ---------------------------------------------------------------------- #
# Utilidades de verificación independiente
# ---------------------------------------------------------------------- #

def trocear_chunks(png):
    """Devuelve [(tipo, datos, crc_leido)] recorriendo los chunks del PNG."""
    if png[:8] != FIRMA:
        raise AssertionError("el PNG no empieza con la firma esperada")
    chunks = []
    posicion = 8
    while posicion < len(png):
        largo = struct.unpack(">I", png[posicion:posicion + 4])[0]
        tipo = png[posicion + 4:posicion + 8]
        datos = png[posicion + 8:posicion + 8 + largo]
        crc_leido = struct.unpack(
            ">I", png[posicion + 8 + largo:posicion + 12 + largo]
        )[0]
        chunks.append((tipo, datos, crc_leido))
        posicion += 12 + largo
    return chunks


def flujo_idat(png):
    """Concatena los datos de todos los chunk IDAT (aquí hay uno solo)."""
    return b"".join(datos for tipo, datos, _ in trocear_chunks(png) if tipo == b"IDAT")


def descomprimir_verificando(png, ancho, alto):
    """Descomprime el IDAT con la stdlib y exige el largo exacto esperado."""
    crudo = zlib.decompress(flujo_idat(png))
    esperado = alto * (1 + ancho * 3)
    assert len(crudo) == esperado, (
        "el flujo descomprimido mide {0} bytes y se esperaban {1}".format(
            len(crudo), esperado
        )
    )
    return crudo


def scanlines_esperadas(ancho, alto, pixeles):
    """Arma el flujo esperado: filtro 0 + fila RGB, repetido por fila."""
    paso = ancho * 3
    salida = bytearray()
    for fila in range(alto):
        salida.append(0)
        salida.extend(pixeles[fila * paso:(fila + 1) * paso])
    return bytes(salida)


def imagen_solida(ancho, alto, color):
    """Búfer RGB de un solo color."""
    return bytes(color) * (ancho * alto)


def imagen_patron(ancho, alto):
    """Ajedrez de bloques de 4x4 con una franja de color que se repite."""
    pixeles = bytearray(ancho * alto * 3)
    for y in range(alto):
        for x in range(ancho):
            bloque = ((x // 4) + (y // 4)) % 2
            if bloque:
                color = (230, 40, 20)
            else:
                color = (15, 90, 200)
            if 40 <= y < 48:
                color = (250, 200, 10) if (x // 8) % 2 else (10, 10, 10)
            posicion = (y * ancho + x) * 3
            pixeles[posicion:posicion + 3] = bytes(color)
    return bytes(pixeles)


def imagen_gradiente(ancho, alto):
    """Gradiente en tres canales: fuerza literales y algunos matches."""
    pixeles = bytearray(ancho * alto * 3)
    for y in range(alto):
        for x in range(ancho):
            posicion = (y * ancho + x) * 3
            pixeles[posicion] = (x * 255) // max(1, ancho - 1)
            pixeles[posicion + 1] = (y * 255) // max(1, alto - 1)
            pixeles[posicion + 2] = (x * 7 + y * 3) % 256
    return bytes(pixeles)


# ---------------------------------------------------------------------- #
# Estructura del archivo
# ---------------------------------------------------------------------- #

@caso
def firma_ihdr_idat_iend_en_orden():
    png = codificar_png(2, 2, imagen_solida(2, 2, (1, 2, 3)))
    assert png[:8] == FIRMA, "la firma PNG es incorrecta"
    chunks = trocear_chunks(png)
    tipos = [tipo for tipo, _, _ in chunks]
    assert tipos == [b"IHDR", b"IDAT", b"IEND"], "orden de chunks inesperado: {0}".format(tipos)
    assert chunks[0][1][:8] == struct.pack(">II", 2, 2), "el IHDR no declara 2x2"
    assert chunks[-1][1] == b"", "el chunk IEND debe ir vacío"
    assert png.endswith(b"IEND" + struct.pack(">I", crc32(b"IEND"))), "IEND mal cerrado"


@caso
def crc32_vector_conocido_y_comparacion_independiente():
    assert crc32(b"123456789") == 0xCBF43926, "CRC-32 no coincide con el vector RFC"
    muestra = b"AREPA es un lenguaje propio"
    assert crc32(muestra) == (binascii.crc32(muestra) & 0xFFFFFFFF), (
        "el CRC-32 propio difiere de la implementación estándar"
    )
    assert crc32(b"") == 0, "el CRC-32 de una entrada vacía debe ser 0"


@caso
def adler32_vector_conocido():
    assert adler32(b"Wikipedia") == 0x11E60398, "Adler-32 no coincide con el vector"
    assert adler32(b"") == 1, "el Adler-32 de una entrada vacía debe ser 1"
    assert adler32(b"abc") == (zlib.adler32(b"abc") & 0xFFFFFFFF), (
        "el Adler-32 propio difiere de la implementación estándar"
    )


@caso
def chunks_llevan_crc_valido():
    png = codificar_png(7, 5, imagen_gradiente(7, 5))
    for tipo, datos, crc_leido in trocear_chunks(png):
        esperado = binascii.crc32(tipo + datos) & 0xFFFFFFFF
        assert crc_leido == esperado, "CRC inválido en el chunk {0!r}".format(tipo)


@caso
def leer_cabecera_devuelve_los_campos():
    png = codificar_png(13, 9, imagen_solida(13, 9, (0, 128, 255)))
    cabecera = leer_cabecera(png)
    assert cabecera["ancho"] == 13, "ancho leído incorrecto"
    assert cabecera["alto"] == 9, "alto leído incorrecto"
    assert cabecera["profundidad"] == 8, "la profundidad debe ser 8"
    assert cabecera["tipo_color"] == 2, "el tipo de color debe ser RGB (2)"
    assert cabecera["interlace"] == 0, "el entrelazado debe ser 0"


@caso
def leer_cabecera_rechaza_firma_ajena():
    try:
        leer_cabecera(b"GIF89a" + b"\x00" * 40)
    except ValueError as problema:
        assert "firma" in str(problema), "el error debe mencionar la firma"
    else:
        raise AssertionError("leer_cabecera debería rechazar datos que no son PNG")


# ---------------------------------------------------------------------- #
# Ida y vuelta de las scanlines
# ---------------------------------------------------------------------- #

@caso
def roundtrip_fijo_conserva_las_scanlines():
    ancho, alto = 9, 6
    pixeles = imagen_gradiente(ancho, alto)
    png = codificar_png(ancho, alto, pixeles, "fijo")
    crudo = descomprimir_verificando(png, ancho, alto)
    esperado = scanlines_esperadas(ancho, alto, pixeles)
    assert crudo == esperado, "las scanlines descomprimidas no coinciden"
    paso = ancho * 3 + 1
    assert crudo[0] == 0, "la primera fila no empieza con filtro 0"
    assert all(crudo[fila * paso] == 0 for fila in range(alto)), (
        "todas las filas deben empezar con el filtro 0"
    )


@caso
def roundtrip_guardado_conserva_las_scanlines():
    ancho, alto = 21, 11
    pixeles = imagen_patron(ancho, alto)
    png = codificar_png(ancho, alto, pixeles, "guardado")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "el modo guardado no reproduce los píxeles"
    )
    # Los bloques stored añaden cabeceras de 5 bytes: nunca comprimen.
    assert len(png) > len(pixeles), "el modo guardado no debería comprimir"


@caso
def roundtrip_guardado_con_mas_de_un_bloque():
    # 250x150 RGB + un filtro por fila supera los 65535 bytes, así que el
    # modo guardado necesita varios bloques BTYPE=00 encadenados.
    ancho, alto = 250, 150
    pixeles = imagen_gradiente(ancho, alto)
    assert alto * (1 + ancho * 3) > 65535, "la prueba debe superar un bloque"
    png = codificar_png(ancho, alto, pixeles, "guardado")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "los bloques guardados múltiples no reproducen los píxeles"
    )


@caso
def color_solido_comprime_de_forma_clara():
    ancho, alto = 200, 100
    pixeles = imagen_solida(ancho, alto, (200, 30, 90))
    png = codificar_png(ancho, alto, pixeles, "fijo")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "la imagen sólida no se reproduce"
    )
    assert len(png) < len(pixeles), (
        "una imagen sólida debería pesar menos que sus píxeles: {0} >= {1}".format(
            len(png), len(pixeles)
        )
    )
    assert len(png) < 1000, "la compresión de una imagen sólida es demasiado pobre"


@caso
def patron_repetitivo_conserva_los_pixeles():
    ancho, alto = 120, 80
    pixeles = imagen_patron(ancho, alto)
    png = codificar_png(ancho, alto, pixeles, "fijo")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "el patrón repetitivo no se reproduce"
    )
    assert len(png) < len(pixeles), "el patrón repetitivo debería comprimir"


@caso
def gradiente_conserva_los_pixeles():
    ancho, alto = 160, 120
    pixeles = imagen_gradiente(ancho, alto)
    png = codificar_png(ancho, alto, pixeles, "fijo")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "el gradiente no se reproduce"
    )
    # Este gradiente es casi todo literales y con Huffman fijo los bytes
    # >= 144 gastan 9 bits, así que puede crecer un poco; lo importante es
    # que el crecimiento quede acotado y no haya matches inválidos.
    assert len(png) < len(pixeles) * 1.2, (
        "el PNG del gradiente creció demasiado: {0} para {1} píxeles".format(
            len(png), len(pixeles)
        )
    )


@caso
def imagen_grande_ejercita_ventana_y_longitudes():
    ancho, alto = 400, 300
    pixeles = bytearray(imagen_patron(ancho, alto))
    # Franja que repite el patrón de hace ~34000 bytes, más allá de la
    # ventana de 32768: el codificador debe seguir eligiendo matches cortos
    # válidos y nunca distancias fuera de rango.
    paso = ancho * 3
    inicio = 200 * paso
    pixeles[inicio:inicio + 5 * paso] = pixeles[inicio - 34 * paso:inicio - 29 * paso]
    pixeles = bytes(pixeles)
    png = codificar_png(ancho, alto, pixeles, "fijo")
    crudo = descomprimir_verificando(png, ancho, alto)
    assert crudo == scanlines_esperadas(ancho, alto, pixeles), (
        "la imagen grande no se reproduce"
    )


@caso
def tamano_descomprimido_es_exacto():
    ancho, alto = 33, 17
    pixeles = imagen_solida(ancho, alto, (0, 0, 0))
    for modo in ("fijo", "guardado"):
        png = codificar_png(ancho, alto, pixeles, modo)
        crudo = zlib.decompress(flujo_idat(png))
        assert len(crudo) == alto * (1 + ancho * 3), (
            "en modo {0} el flujo mide {1} y debía medir {2}".format(
                modo, len(crudo), alto * (1 + ancho * 3)
            )
        )


# ---------------------------------------------------------------------- #
# Validaciones de entrada
# ---------------------------------------------------------------------- #

@caso
def error_por_longitud_incorrecta_de_pixeles():
    try:
        codificar_png(4, 4, b"\x00" * 10)
    except ValueError as problema:
        mensaje = str(problema)
        assert "48" in mensaje, "el error debe indicar los 48 bytes esperados"
        assert "10" in mensaje, "el error debe indicar los 10 bytes recibidos"
    else:
        raise AssertionError("debería rechazar un búfer de píxeles incompleto")


@caso
def error_por_dimensiones_no_positivas():
    for ancho, alto, nombre in ((0, 5, "ancho"), (5, 0, "alto"), (-2, 3, "ancho")):
        try:
            codificar_png(ancho, alto, b"\x00" * max(0, ancho * alto * 3))
        except ValueError as problema:
            assert nombre in str(problema), (
                "el error debe mencionar {0}: {1}".format(nombre, problema)
            )
        else:
            raise AssertionError(
                "debería rechazar ancho={0} y alto={1}".format(ancho, alto)
            )


@caso
def error_por_compresion_desconocida():
    try:
        codificar_png(2, 2, b"\x00" * 12, "zip")
    except ValueError as problema:
        mensaje = str(problema)
        assert "compresión" in mensaje and "zip" in mensaje, (
            "el error debe mencionar el modo recibido: {0}".format(mensaje)
        )
    else:
        raise AssertionError("debería rechazar una compresión desconocida")


@caso
def error_por_tipo_de_pixeles_incorrecto():
    try:
        codificar_png(2, 2, [0] * 12)
    except ValueError as problema:
        assert "pixeles" in str(problema), "el error debe mencionar 'pixeles'"
    else:
        raise AssertionError("debería rechazar una lista en lugar de bytes")


# ---------------------------------------------------------------------- #
# Escritura en disco
# ---------------------------------------------------------------------- #

@caso
def escribir_png_crea_directorios_y_devuelve_tamano():
    carpeta = tempfile.mkdtemp(prefix="arepa_png_")
    try:
        ruta = os.path.join(carpeta, "anidada", "salida", "imagen.png")
        ancho, alto = 24, 12
        pixeles = imagen_gradiente(ancho, alto)
        escritos = escribir_png(ruta, ancho, alto, pixeles)
        assert os.path.isfile(ruta), "el archivo PNG no se creó"
        assert escritos == os.path.getsize(ruta), (
            "escribir_png devolvió {0} y el archivo mide {1}".format(
                escritos, os.path.getsize(ruta)
            )
        )
        with open(ruta, "rb") as archivo:
            en_disco = archivo.read()
        assert en_disco == codificar_png(ancho, alto, pixeles), (
            "el archivo no coincide con codificar_png"
        )
        assert leer_cabecera(en_disco)["ancho"] == ancho, "cabecera en disco incorrecta"
        assert descomprimir_verificando(en_disco, ancho, alto) == scanlines_esperadas(
            ancho, alto, pixeles
        ), "el PNG en disco no se descomprime a los píxeles originales"
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@caso
def escribir_png_respeta_el_modo_guardado():
    carpeta = tempfile.mkdtemp(prefix="arepa_png_")
    try:
        ruta = os.path.join(carpeta, "guardado.png")
        pixeles = imagen_solida(16, 8, (9, 9, 9))
        escritos = escribir_png(ruta, 16, 8, pixeles, "guardado")
        with open(ruta, "rb") as archivo:
            en_disco = archivo.read()
        assert escritos == len(en_disco), "el tamaño devuelto no coincide"
        assert descomprimir_verificando(en_disco, 16, 8) == scanlines_esperadas(
            16, 8, pixeles
        ), "el archivo guardado no se descomprime correctamente"
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------------- #
# Utilidades del motor de gráficas
# ---------------------------------------------------------------------- #

def color_en(pixeles, ancho, x, y):
    """Color RGB del píxel (x, y) de un búfer ya capturado."""
    inicio = (y * ancho + x) * 3
    return tuple(pixeles[inicio:inicio + 3])


def verificar_png_valido(lienzo, ancho, alto):
    """Comprueba cabecera, tamaño descomprimido y contenido no vacío."""
    assert lienzo.ancho == ancho and lienzo.alto == alto, (
        "el lienzo mide {0}x{1} y se esperaba {2}x{3}".format(
            lienzo.ancho, lienzo.alto, ancho, alto
        )
    )
    png = lienzo.png()
    cabecera = leer_cabecera(png)
    assert cabecera["ancho"] == ancho and cabecera["alto"] == alto, (
        "la cabecera del PNG no declara {0}x{1}".format(ancho, alto)
    )
    assert cabecera["profundidad"] == 8 and cabecera["tipo_color"] == 2, (
        "el PNG debe ser RGB de 8 bits"
    )
    crudo = zlib.decompress(flujo_idat(png))
    esperado = alto * (1 + ancho * 3)
    assert len(crudo) == esperado, (
        "el flujo descomprimido mide {0} y se esperaban {1}".format(
            len(crudo), esperado
        )
    )
    assert any(byte != 255 for byte in lienzo.pixeles()), (
        "la gráfica salió completamente blanca"
    )
    return png


def grupos_de_color(lienzo, color):
    """Agrupa columnas contiguas que contienen 'color'.

    Devuelve [(x_izquierda, x_derecha, y_superior)] por cada barra. Se
    usa para medir alturas sin depender de coordenadas fijas.
    """
    pixeles = lienzo.pixeles()
    ancho, alto = lienzo.ancho, lienzo.alto
    superiores = []
    for x in range(ancho):
        minimo = None
        for y in range(alto):
            if color_en(pixeles, ancho, x, y) == color:
                minimo = y
                break
        superiores.append(minimo)

    grupos = []
    inicio = None
    minimo = None
    for x, valor in enumerate(superiores):
        if valor is not None:
            if inicio is None:
                inicio = x
                minimo = valor
            elif valor < minimo:
                minimo = valor
        elif inicio is not None:
            grupos.append((inicio, x - 1, minimo))
            inicio = None
    if inicio is not None:
        grupos.append((inicio, ancho - 1, minimo))
    return grupos


# ---------------------------------------------------------------------- #
# Fuente bitmap
# ---------------------------------------------------------------------- #

@caso
def fuente_mide_texto_con_escala_y_multilinea():
    assert ancho_texto("") == 0, "el texto vacío no debe medir nada"
    assert ancho_texto("A") == 5, "un glifo debe medir 5 px"
    assert ancho_texto("AB") == 11, "dos glifos deben medir 5 + 1 + 5"
    assert ancho_texto("AB", 2) == 22, "la escala debe duplicar el ancho"
    assert ancho_texto("Hola\nMundo!") == ancho_texto("Mundo!"), (
        "con varias líneas debe mandar la más ancha"
    )
    assert alto_texto() == 7 and alto_texto(3) == 21, "alto de texto incorrecto"


@caso
def fuente_normaliza_tildes_y_simbolos():
    assert normalizar_texto("canción") == "cancion", "no quitó la tilde"
    assert normalizar_texto("Ñandú") == "Nandu", "no resolvió la eñe"
    assert normalizar_texto("¿Qué? ¡Sí!") == "?Que? !Si!", (
        "los signos de apertura deben pasar a ASCII: {0!r}".format(
            normalizar_texto("¿Qué? ¡Sí!")
        )
    )
    assert normalizar_texto("“hola” – 1") == '"hola" - 1', (
        "comillas y rayas tipográficas mal normalizadas"
    )
    assert normalizar_texto("emojis 🙂") == "emojis ?", (
        "lo no representable debe sustituirse por '?'"
    )
    assert filas("á") == filas("a"), "la 'á' debe usar el glifo de 'a'"
    assert filas("ñ") == filas("n"), "la 'ñ' debe usar el glifo de 'n'"


@caso
def fuente_cubre_todo_el_ascii_imprimible():
    assert len(GLIFOS) == 95, "deben existir 95 glifos imprimibles"
    for codigo in range(32, 127):
        assert codigo in GLIFOS, "falta el glifo {0!r}".format(chr(codigo))
        glifo = GLIFOS[codigo]
        assert len(glifo) == 7, (
            "el glifo {0!r} no tiene 7 filas".format(chr(codigo))
        )
        for fila in glifo:
            assert 0 <= fila < 32, (
                "el glifo {0!r} tiene una fila de más de 5 bits".format(
                    chr(codigo)
                )
            )
    assert GLIFOS[ord(" ")] == (0,) * 7, "el espacio debe estar vacío"
    assert any(GLIFOS[ord("A")]), "la 'A' no puede ser un glifo vacío"


# ---------------------------------------------------------------------- #
# Lienzo
# ---------------------------------------------------------------------- #

@caso
def lienzo_dimensiones_del_buffer():
    lienzo = Lienzo(13, 7)
    pixeles = lienzo.pixeles()
    assert len(pixeles) == 13 * 7 * 3, "el búfer no mide ancho*alto*3"
    assert set(pixeles) == {255}, "el fondo por defecto debe ser blanco"
    lienzo.poner(0, 0, (0, 0, 0))
    assert color_en(lienzo.pixeles(), 13, 0, 0) == (0, 0, 0), (
        "poner no cambió el píxel"
    )


@caso
def lienzo_recorta_todos_los_bordes():
    lienzo = Lienzo(20, 20)
    lienzo.poner(-5, -5, (0, 0, 0))
    lienzo.poner(25, 25, (0, 0, 0))
    lienzo.circulo_relleno(-3, -3, 5, (0, 255, 0))
    lienzo.linea(-10, -10, 10, 10, (255, 0, 0))
    lienzo.rectangulo_relleno(-5, -5, 10, 10, (0, 0, 255))
    lienzo.rectangulo(-4, 15, 30, 10, (0, 0, 0))
    pixeles = lienzo.pixeles()
    assert len(pixeles) == 20 * 20 * 3, "el recorte alteró el búfer"
    assert color_en(pixeles, 20, 0, 0) == (0, 0, 255), (
        "el rectángulo recortado no pintó la esquina"
    )
    assert color_en(pixeles, 20, 19, 15) == (0, 0, 0), (
        "el contorno recortado no llegó al borde superior"
    )


@caso
def lienzo_lineas_horizontal_vertical_y_diagonal():
    horizontal = Lienzo(20, 20)
    horizontal.linea(2, 5, 15, 5, (10, 20, 30))
    for x in range(2, 16):
        assert color_en(horizontal.pixeles(), 20, x, 5) == (10, 20, 30), (
            "falta un píxel de la línea horizontal en x={0}".format(x)
        )

    vertical = Lienzo(20, 20)
    vertical.linea(8, 1, 8, 18, (40, 50, 60))
    for y in range(1, 19):
        assert color_en(vertical.pixeles(), 20, 8, y) == (40, 50, 60), (
            "falta un píxel de la línea vertical en y={0}".format(y)
        )

    diagonal = Lienzo(20, 20)
    diagonal.linea(0, 0, 9, 9, (70, 80, 90))
    for paso in range(10):
        assert color_en(diagonal.pixeles(), 20, paso, paso) == (70, 80, 90), (
            "la diagonal de Bresenham se desvió en {0}".format(paso)
        )


@caso
def lienzo_rectangulo_relleno_y_contorno():
    relleno = Lienzo(30, 20)
    relleno.rectangulo_relleno(5, 4, 10, 6, (200, 30, 40))
    pixeles = relleno.pixeles()
    for y in range(4, 10):
        for x in range(5, 15):
            assert color_en(pixeles, 30, x, y) == (200, 30, 40), (
                "falta el relleno en ({0}, {1})".format(x, y)
            )
    assert color_en(pixeles, 30, 4, 4) == (255, 255, 255), (
        "el relleno se salió por la izquierda"
    )
    assert color_en(pixeles, 30, 15, 4) == (255, 255, 255), (
        "el relleno se salió por la derecha"
    )

    contorno = Lienzo(30, 20)
    contorno.rectangulo(5, 4, 10, 6, (0, 0, 0))
    pixeles = contorno.pixeles()
    assert color_en(pixeles, 30, 5, 4) == (0, 0, 0), "falta la esquina"
    assert color_en(pixeles, 30, 14, 9) == (0, 0, 0), "falta la esquina opuesta"
    assert color_en(pixeles, 30, 8, 6) == (255, 255, 255), (
        "el contorno no debe rellenar el interior"
    )


@caso
def lienzo_circulo_relleno_y_simetria():
    lienzo = Lienzo(40, 40)
    lienzo.circulo_relleno(20, 20, 5, (0, 0, 0))
    pixeles = lienzo.pixeles()
    assert color_en(pixeles, 40, 20, 20) == (0, 0, 0), "falta el centro"
    for desplazamiento in (-5, -3, 0, 3, 5):
        assert color_en(
            pixeles, 40, 20 + desplazamiento, 20
        ) == (0, 0, 0), "el ecuador del círculo quedó incompleto"
        assert color_en(
            pixeles, 40, 20, 20 + desplazamiento
        ) == (0, 0, 0), "el meridiano del círculo quedó incompleto"
    assert color_en(pixeles, 40, 26, 20) == (255, 255, 255), (
        "el círculo se salió del radio"
    )
    assert color_en(pixeles, 40, 24, 24) == (255, 255, 255), (
        "la esquina del cuadro no debe pintarse"
    )
    pintados = sum(
        1 for y in range(40) for x in range(40)
        if color_en(pixeles, 40, x, y) == (0, 0, 0)
    )
    assert 60 <= pintados <= 110, (
        "el área del círculo r=5 es sospechosa: {0} píxeles".format(pintados)
    )


@caso
def lienzo_texto_visible_y_multilinea():
    lienzo = Lienzo(200, 60)
    texto = "AREPA 2026"
    lienzo.texto(5, 5, texto)
    pixeles = lienzo.pixeles()
    pintados = sum(1 for byte in pixeles if byte != 255)
    assert pintados > 100, "el texto no dejó suficientes píxeles visibles"
    max_x = max_y = -1
    for y in range(lienzo.alto):
        for x in range(lienzo.ancho):
            if color_en(pixeles, lienzo.ancho, x, y) != (255, 255, 255):
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    assert max_x <= 5 + ancho_texto(texto) - 1, "el texto se sale a la derecha"
    assert max_y <= 5 + alto_texto() - 1, "el texto se sale por abajo"

    multilinea = Lienzo(100, 60)
    multilinea.texto(2, 2, "Arriba\nAbajo")
    pixeles = multilinea.pixeles()
    assert any(
        color_en(pixeles, 100, x, y) != (255, 255, 255)
        for y in range(11, 18) for x in range(2, 40)
    ), "la segunda línea no se dibujó debajo de la primera"


@caso
def lienzo_rechaza_colores_invalidos():
    for color in ((256, 0, 0), (-1, 0, 0), (1, 2), "rojo", (1.5, 2, 3)):
        try:
            Lienzo(4, 4).poner(0, 0, color)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "debería rechazar el color {0!r}".format(color)
            )


# ---------------------------------------------------------------------- #
# Escalas
# ---------------------------------------------------------------------- #

@caso
def escalas_mapeo_lineal_e_inverso():
    escala = EscalaLineal(0, 10, 100, 200)
    assert escala.mapear(0) == 100, "el mínimo debe caer en rango_min"
    assert escala.mapear(10) == 200, "el máximo debe caer en rango_max"
    assert escala.mapear(5) == 150, "el punto medio debe caer en el centro"
    assert escala.invertir(150) == 5, "invertir no deshace el mapeo"
    for valor in (0.5, 3.3, 9.99):
        assert abs(escala.invertir(escala.mapear(valor)) - valor) < 1e-9, (
            "ida y vuelta imprecisa para {0}".format(valor)
        )


@caso
def escalas_dominio_degenerado_y_no_finitos():
    escala = EscalaLineal(5, 5, 0, 100)
    assert abs(escala.dominio_min - 4.5) < 1e-9, "no expandió el dominio"
    assert abs(escala.dominio_max - 5.5) < 1e-9, "no expandió el dominio"
    assert escala.mapear(5) == 50, "el valor degenerado debe quedar al centro"

    cero = EscalaLineal(0, 0, 0, 100)
    assert cero.dominio_min == -1 and cero.dominio_max == 1, (
        "un dominio cero debe expandirse a +-1"
    )
    assert cero.mapear(0) == 50, "el cero debe quedar al centro"

    for malo in (float("nan"), float("inf"), float("-inf")):
        try:
            EscalaLineal(malo, 10, 0, 100)
        except ValueError:
            pass
        else:
            raise AssertionError("debería rechazar el dominio {0!r}".format(malo))
        try:
            escala.mapear(malo)
        except ValueError:
            pass
        else:
            raise AssertionError("debería rechazar el valor {0!r}".format(malo))


@caso
def escalas_ticks_bonitos_y_formateo():
    escala = EscalaLineal(0, 100, 0, 100)
    assert escala.ticks(5) == [0, 20, 40, 60, 80, 100], (
        "los ticks de 0..100 deben ir de 20 en 20: {0}".format(escala.ticks(5))
    )
    fina = EscalaLineal(0, 1, 0, 100)
    marcas = fina.ticks(5)
    assert marcas[0] == 0 and abs(marcas[-1] - 1) < 1e-9, (
        "los ticks deben cubrir el dominio: {0}".format(marcas)
    )
    for marca in marcas:
        multiplo = marca / 0.2
        assert abs(multiplo - round(multiplo)) < 1e-6, (
            "el tick {0} no es múltiplo del paso 0.2".format(marca)
        )

    assert formatear(0) == "0", "el cero debe ser '0'"
    assert formatear(-3) == "-3", "los enteros van sin decimales"
    assert formatear(1500.0) == "1500", "los enteros van sin decimales"
    assert formatear(2.5) == "2.5", "un decimal debe conservarse"
    assert formatear(0.25) == "0.25", "dos decimales deben conservarse"
    assert "e" in formatear(12345678), "los valores extremos usan notación científica"
    assert formatear(float("nan")) == "nada", "NaN debe mostrarse como 'nada'"


@caso
def escalas_banda_centros_y_validaciones():
    banda = EscalaBanda(["A", "B", "C"], 0, 300)
    assert banda.ancho_banda == 100, "el ancho de banda debe ser 100"
    assert banda.posiciones() == [50, 150, 250], "centros de banda incorrectos"
    assert banda.mapear("B") == 150, "mapear debe devolver el centro"
    assert banda.mapear("A") == 50, "mapear la primera categoría falló"
    try:
        banda.mapear("Z")
    except ValueError:
        pass
    else:
        raise AssertionError("debería rechazar una categoría desconocida")
    try:
        EscalaBanda(["A", "A"], 0, 100)
    except ValueError:
        pass
    else:
        raise AssertionError("debería rechazar categorías repetidas")


# ---------------------------------------------------------------------- #
# Gráficas: los cinco tipos generan un PNG válido
# ---------------------------------------------------------------------- #

@caso
def barras_genera_png_valido():
    series = [
        Serie(
            "Ventas",
            ["Bogotá", "Medellín", "Cali", "Barranquilla"],
            [120, 90, 60, 45],
        )
    ]
    lienzo = dibujar(
        "barras",
        series,
        titulo="Ventas por ciudad",
        etiqueta_x="Ciudad",
        etiqueta_y="Millones",
    )
    verificar_png_valido(lienzo, 800, 480)
    assert bytes(PALETA[0]) in lienzo.pixeles(), "no se pintaron las barras"


@caso
def lineas_genera_png_valido_con_dos_series():
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
    lienzo = dibujar(
        "lineas",
        [
            Serie("2025", meses, [40, 46, 52, 58, 66, 72]),
            Serie("2026", meses, [48, 55, 63, 60, 74, 81]),
        ],
        titulo="Evolución mensual",
        etiqueta_x="Mes",
        etiqueta_y="Ingresos",
    )
    verificar_png_valido(lienzo, 800, 480)
    pixeles = lienzo.pixeles()
    assert bytes(PALETA[0]) in pixeles, "falta la primera línea"
    assert bytes(PALETA[1]) in pixeles, "falta la segunda línea"


@caso
def histograma_genera_png_valido():
    valores = [((indice * 37) % 100) for indice in range(100)]
    lienzo = dibujar(
        "histograma",
        [Serie("Tiempos", None, valores)],
        titulo="Distribución de tiempos",
        etiqueta_x="Minutos",
        etiqueta_y="Frecuencia",
    )
    verificar_png_valido(lienzo, 800, 480)
    assert bytes(PALETA[0]) in lienzo.pixeles(), "no se pintaron las cubetas"


@caso
def dispersion_genera_png_valido():
    xs = list(range(1, 61))
    ys = [2 * x + ((x * 7) % 9) for x in xs]
    lienzo = dibujar(
        "dispersion",
        [Serie("Muestras", xs, ys)],
        titulo="Publicidad vs. ventas",
        etiqueta_x="Inversión",
        etiqueta_y="Ventas",
    )
    verificar_png_valido(lienzo, 800, 480)
    assert bytes(PALETA[0]) in lienzo.pixeles(), "no se pintaron los puntos"


@caso
def cajas_genera_png_valido():
    categorias = ["Norte", "Sur", "Centro", "Occidente"]
    xs = []
    ys = []
    for indice, categoria in enumerate(categorias):
        for posicion in range(30):
            xs.append(categoria)
            ys.append(indice * 10 + (posicion % 15))
    lienzo = dibujar(
        "cajas",
        [Serie("Salarios", xs, ys)],
        titulo="Salarios por zona",
        etiqueta_x="Zona",
        etiqueta_y="Salario",
    )
    verificar_png_valido(lienzo, 800, 480)
    assert bytes(PALETA[0]) in lienzo.pixeles(), "no se pintó la primera caja"
    assert bytes(PALETA[1]) in lienzo.pixeles(), "no se pintó la segunda caja"

    # El agrupamiento también aplica a x numérica con valores repetidos
    # (décadas, años): dos grupos deben producir dos cajas de colores
    # distintos, no una sola caja por serie.
    xs = [1940] * 10 + [1950] * 10
    ys = [100 + i for i in range(10)] + [200 + i for i in range(10)]
    lienzo = dibujar(
        "cajas",
        [Serie("Pasajeros", xs, ys)],
        titulo="Décadas numéricas",
        etiqueta_x="Década",
        etiqueta_y="Pasajeros",
    )
    verificar_png_valido(lienzo, 800, 480)
    assert bytes(PALETA[0]) in lienzo.pixeles(), "falta la caja de 1940"
    assert bytes(PALETA[1]) in lienzo.pixeles(), "falta la caja de 1950"


# ---------------------------------------------------------------------- #
# Gráficas: comportamiento de los datos
# ---------------------------------------------------------------------- #

@caso
def barras_suma_categorias_repetidas():
    lienzo = dibujar(
        "barras",
        [Serie("Totales", ["A", "B", "A"], [10, 20, 30])],
        titulo="Categorías repetidas",
    )
    grupos = grupos_de_color(lienzo, PALETA[0])
    assert len(grupos) == 2, (
        "deben quedar dos barras (A y B); hay {0}".format(len(grupos))
    )
    base = lienzo.alto - 64
    alto_a = base - grupos[0][2] + 1
    alto_b = base - grupos[1][2] + 1
    assert 1.9 <= alto_a / alto_b <= 2.1, (
        "A debe sumar 40 y B 20 (relación 2); alturas {0} y {1}".format(
            alto_a, alto_b
        )
    )


@caso
def histograma_usa_las_cubetas_esperadas():
    valores = list(range(100))
    bordes, conteos = cubetas_histograma(valores)
    esperado = max(5, min(20, math.ceil(math.sqrt(len(valores)))))
    assert len(conteos) == esperado, (
        "se esperaban {0} cubetas y hay {1}".format(esperado, len(conteos))
    )
    assert len(bordes) == len(conteos) + 1, "faltan bordes de cubeta"
    assert sum(conteos) == len(valores), "se perdió algún valor"
    assert bordes[0] == 0 and bordes[-1] == 99, "los bordes no cubren los datos"
    assert all(
        bordes[indice] < bordes[indice + 1]
        for indice in range(len(bordes) - 1)
    ), "los bordes deben ser crecientes"

    bordes, conteos = cubetas_histograma(valores, cantidad=7)
    assert len(conteos) == 7, "la cantidad explícita no se respetó"
    assert sum(conteos) == 100, "se perdió algún valor con cantidad=7"


@caso
def cajas_cuartiles_con_datos_conocidos():
    assert cuartiles([1, 2, 3, 4, 5]) == (2.0, 3.0, 4.0), (
        "cuartiles de 1..5 incorrectos"
    )
    assert cuartiles([1, 2, 3, 4]) == (1.75, 2.5, 3.25), (
        "la interpolación lineal de cuartiles es incorrecta"
    )
    assert cuartiles([7]) == (7.0, 7.0, 7.0), "un solo valor debe dar tres 7"
    assert cuartiles([1, "nada", 3, None, 2]) == (1.5, 2.0, 2.5), (
        "debe ignorar vacíos y 'nada'"
    )
    try:
        cuartiles([None, "nada"])
    except ValueError:
        pass
    else:
        raise AssertionError("debería rechazar una lista sin números")


# ---------------------------------------------------------------------- #
# Etiquetas del eje x: se espacian, no se truncan en bloque
# ---------------------------------------------------------------------- #

@caso
def eje_x_espacia_etiquetas_largas_sin_recortarlas():
    posiciones = [78.0 + indice * (698.0 / 11) for indice in range(12)]
    etiquetas = [
        "2026-01-{0:02d}".format(5 + indice) for indice in range(12)
    ]
    indices = _seleccionar_etiquetas(posiciones, etiquetas, 54)
    assert len(indices) < 12, (
        "con 12 fechas de 10 caracteres deben mostrarse menos etiquetas"
    )
    assert len(indices) >= 4, "se descartaron demasiadas etiquetas"
    assert indices[0] == 0, "la primera etiqueta debe mostrarse"
    assert indices[-1] == 11, "se debe procurar incluir la última etiqueta"
    for indice in indices:
        assert not etiquetas[indice].endswith("..."), (
            "ninguna etiqueta visible debe quedar truncada"
        )
    for izquierda, derecha in zip(indices, indices[1:]):
        assert posiciones[derecha] - posiciones[izquierda] >= (
            ancho_texto(etiquetas[derecha]) + 8
        ), "dos etiquetas visibles se solapan"


@caso
def eje_x_solo_recorta_si_no_cabe_en_toda_el_area():
    enorme = "X" * 150
    recortada = _acortar_etiqueta(enorme, 698)
    assert recortada.endswith("..."), (
        "una etiqueta más ancha que el área sí debe recortarse"
    )
    assert ancho_texto(recortada) <= 698, "el recorte no respetó el área"
    assert _acortar_etiqueta("Bogotá", 698) == "Bogotá", (
        "una etiqueta que cabe no debe tocarse"
    )
    assert _acortar_etiqueta("2026-01-05", 50) == "01-05", (
        "una fecha ISO larga debe preferir su forma corta"
    )


@caso
def eje_x_conserva_todas_las_etiquetas_cortas():
    posiciones = [100.0, 300.0, 500.0]
    etiquetas = ["Ene", "Feb", "Mar"]
    assert _seleccionar_etiquetas(posiciones, etiquetas, 200) == [0, 1, 2], (
        "con etiquetas cortas deben mostrarse todas"
    )
    assert _seleccionar_etiquetas([100.0], ["Ene"], 200) == [0], (
        "una sola etiqueta siempre se muestra"
    )


# ---------------------------------------------------------------------- #
# Gráficas: errores de entrada
# ---------------------------------------------------------------------- #

@caso
def serie_con_longitudes_distintas_lanza_error():
    try:
        Serie("Rota", [1, 2, 3], [1, 2])
    except ValueError as problema:
        assert "deben coincidir" in str(problema), (
            "el error debe explicar la longitud: {0}".format(problema)
        )
    else:
        raise AssertionError("debería rechazar x e y de distinta longitud")


@caso
def grafica_sin_datos_lanza_error():
    mensaje = "La gráfica no tiene datos numéricos para dibujar."
    casos = [
        Grafica("barras", []),
        Grafica("lineas", [Serie("Vacía", None, [])]),
        Grafica("barras", [Serie("Nada", ["A", "B"], [None, "nada"])]),
        Grafica("histograma", [Serie("NaN", None, [float("nan"), float("inf")])]),
    ]
    for grafica in casos:
        try:
            grafica.renderizar()
        except ValueError as problema:
            assert str(problema) == mensaje, (
                "mensaje inesperado: {0}".format(problema)
            )
        else:
            raise AssertionError(
                "debería rechazar una gráfica sin datos ({0})".format(
                    grafica.tipo
                )
            )


@caso
def tipo_de_grafica_desconocido_lanza_error():
    try:
        Grafica("tarta", [])
    except ValueError as problema:
        texto = str(problema)
        assert "tarta" in texto, "el error debe mencionar el tipo recibido"
        assert all(tipo in texto for tipo in TIPOS), (
            "el error debe listar los tipos válidos: {0}".format(texto)
        )
    else:
        raise AssertionError("debería rechazar un tipo desconocido")


# ---------------------------------------------------------------------- #
# Integración con el runtime: 'pinte' genera archivos PNG reales
# ---------------------------------------------------------------------- #

RUTA_VENTAS = os.path.join(RAIZ, "datos", "ventas.csv").replace("\\", "/")


def correr(programa):
    """Parsea y ejecuta un programa; devuelve el ejecutor."""
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa no parseó: {0}".format(errores)
    ejecutor = EjecutorArepa()
    ejecutor.ejecutar(arbol)
    return ejecutor


def correr_y_fallar(programa):
    """Ejecuta un programa que debe fallar en runtime; devuelve el error."""
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa debería fallar en ejecución, no en parseo"
    try:
        EjecutorArepa().ejecutar(arbol)
    except ErrorGrafica as problema:
        return problema
    raise AssertionError("el programa debería haber fallado: " + programa)


def abrir_ventas():
    """Prefijo de programa que carga la tabla real de ventas."""
    return 'quihubo\nventas = monte "{0}" con encabezado\n'.format(RUTA_VENTAS)


def verificar_png_en_disco(ruta):
    """Comprueba que el archivo es un PNG RGB de 800x480 con contenido."""
    assert os.path.isfile(ruta), "no se creó el PNG: {0}".format(ruta)
    with open(ruta, "rb") as archivo:
        png = archivo.read()
    assert png[:8] == FIRMA, "el archivo no empieza con la firma PNG"
    cabecera = leer_cabecera(png)
    assert (cabecera["ancho"], cabecera["alto"]) == (800, 480), (
        "el PNG mide {0}x{1} y se esperaban 800x480".format(
            cabecera["ancho"], cabecera["alto"]
        )
    )
    assert cabecera["profundidad"] == 8 and cabecera["tipo_color"] == 2, (
        "el PNG debe ser RGB de 8 bits"
    )
    crudo = descomprimir_verificando(png, 800, 480)
    assert any(byte != 255 for byte in crudo), "el PNG salió completamente blanco"
    return png


@caso
def runtime_barras_guardela_escribe_png_y_registra_archivo():
    carpeta = tempfile.mkdtemp(prefix="arepa_pinte_")
    try:
        ruta = os.path.join(carpeta, "barras.png")
        programa = (
            abrir_ventas()
            + 'pinte barras ventas\n titulo "Ventas"\n ejex ciudad\n'
            + " ejey unidades\n guardela \"{0}\"\nchao\n".format(ruta)
        )
        ejecutor = correr(programa)
        verificar_png_en_disco(ruta)
        texto = "\n".join(ejecutor.contexto.salida)
        assert ruta in texto, "el mensaje no menciona la ruta: {0}".format(texto)
        assert "guardada en" in texto and "800x480" in texto, (
            "mensaje de guardado inesperado: {0}".format(texto)
        )
        registros = [
            archivo
            for archivo in ejecutor.contexto.archivos_generados
            if archivo["tipo"] == "png"
        ]
        assert len(registros) == 1, "debe quedar un PNG registrado"
        assert registros[0]["ruta"] == ruta, "la ruta registrada no coincide"
        assert registros[0]["bytes"] == os.path.getsize(ruta), (
            "los bytes registrados no coinciden con el archivo"
        )
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@caso
def runtime_los_cinco_tipos_generan_png_valido():
    carpeta = tempfile.mkdtemp(prefix="arepa_pinte_")
    programas = {
        "barras": "ejex ciudad\nejey unidades",
        "lineas": "ejex fecha\nejey unidades",
        "histograma": "ejey unidades",
        "dispersion": "ejex precio\nejey unidades",
        "cajas": "ejex ciudad\nejey precio",
    }
    try:
        for tipo, clausulas in programas.items():
            ruta = os.path.join(carpeta, "{0}.png".format(tipo))
            programa = (
                abrir_ventas()
                + "pinte {0} ventas\n{1}\nguardela \"{2}\"\nchao\n".format(
                    tipo, clausulas, ruta
                )
            )
            correr(programa)
            verificar_png_en_disco(ruta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@caso
def runtime_ejey_con_lista_genera_dos_series():
    carpeta = tempfile.mkdtemp(prefix="arepa_pinte_")
    try:
        ruta = os.path.join(carpeta, "dos_series.png")
        programa = (
            abrir_ventas()
            + "pinte lineas ventas\n ejex fecha\n ejey [unidades, precio]\n"
            + " leyenda \"Dos series\"\n guardela \"{0}\"\nchao\n".format(ruta)
        )
        ejecutor = correr(programa)
        png = verificar_png_en_disco(ruta)
        # La leyenda de dos series usa los dos primeros colores de la paleta.
        crudo = descomprimir_verificando(png, 800, 480)
        for color in (PALETA[0], PALETA[1]):
            assert bytes(color) in crudo, (
                "falta el color {0} de una de las dos series".format(color)
            )
        assert "lineas" in "\n".join(ejecutor.contexto.salida)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@caso
def runtime_muestrela_escribe_en_salidas_sin_ventana():
    ruta = os.path.join(RAIZ, "salidas", "ventas_barras.png")
    anterior = os.environ.get("AREPA_SIN_VENTANA")
    os.environ["AREPA_SIN_VENTANA"] = "1"
    try:
        programa = (
            abrir_ventas()
            + "pinte barras ventas\n ejex ciudad\n ejey unidades\n"
            + "muestrela\nchao\n"
        )
        ejecutor = correr(programa)
        verificar_png_en_disco(ruta)
        texto = "\n".join(ejecutor.contexto.salida)
        relativa = os.path.join("salidas", "ventas_barras.png")
        assert relativa in texto, "el mensaje no menciona la ruta: {0}".format(texto)
        assert "No hay entorno grafico" in texto, (
            "sin ventana debe avisar que no abrió el visor: {0}".format(texto)
        )
        assert any(
            archivo["ruta"] == relativa and archivo["tipo"] == "png"
            for archivo in ejecutor.contexto.archivos_generados
        ), "muestrela debe registrar el PNG"
    finally:
        if anterior is None:
            os.environ.pop("AREPA_SIN_VENTANA", None)
        else:
            os.environ["AREPA_SIN_VENTANA"] = anterior
        if os.path.isfile(ruta):
            os.remove(ruta)


@caso
def runtime_columna_inexistente_en_ejey_falla():
    programa = (
        abrir_ventas()
        + "pinte barras ventas\n ejex ciudad\n ejey no_existe\nchao\n"
    )
    _, arbol, errores = analizar(programa)
    assert not errores, "el error debe ser de ejecución"
    try:
        EjecutorArepa().ejecutar(arbol)
    except ErrorColumna as problema:
        assert "no_existe" in problema.mensaje, (
            "el error debe nombrar la columna: {0}".format(problema.mensaje)
        )
        assert "ciudad" in problema.mensaje, "el error debe listar las columnas"
    else:
        raise AssertionError("debería fallar con una columna inexistente")


@caso
def runtime_columna_textual_en_ejey_falla():
    programa = abrir_ventas() + "pinte barras ventas\n ejey ciudad\nchao\n"
    problema = correr_y_fallar(programa)
    assert "ciudad" in problema.mensaje, "el error debe nombrar la columna"
    assert "texto" in problema.mensaje, "el error debe indicar el tipo"
    assert "unidades" in problema.mensaje, (
        "el error debe listar las columnas numéricas válidas"
    )


@caso
def runtime_histograma_con_dos_columnas_falla():
    programa = (
        abrir_ventas()
        + "pinte histograma ventas\n ejey [unidades, precio]\nchao\n"
    )
    problema = correr_y_fallar(programa)
    assert "exactamente una" in problema.mensaje, (
        "el error debe explicar que el histograma usa una sola columna: {0}".format(
            problema.mensaje
        )
    )


@caso
def runtime_ruta_sin_png_falla():
    programa = (
        abrir_ventas()
        + "pinte barras ventas\n ejey unidades\n guardela \"salidas/x.jpg\"\n"
        + "chao\n"
    )
    problema = correr_y_fallar(programa)
    assert ".png" in problema.mensaje, "el error debe pedir la extensión .png"
    assert "x.jpg" in problema.mensaje, "el error debe mostrar la ruta recibida"


@caso
def runtime_tabla_vacia_falla():
    programa = "quihubo\nv = arme [a, b]\npinte barras v\nchao\n"
    problema = correr_y_fallar(programa)
    assert "no tiene filas" in problema.mensaje, (
        "el error debe explicar que la tabla está vacía: {0}".format(
            problema.mensaje
        )
    )


@caso
def runtime_titulo_y_leyenda_en_cualquier_orden_cambian_el_png():
    carpeta = tempfile.mkdtemp(prefix="arepa_pinte_")
    try:
        sin_titulo = os.path.join(carpeta, "sin_titulo.png")
        con_titulo = os.path.join(carpeta, "con_titulo.png")
        base = abrir_ventas() + "pinte barras ventas\n ejex ciudad\n ejey unidades\n"
        correr(base + 'guardela "{0}"\nchao\n'.format(sin_titulo))
        # Leyenda antes que título y ejey antes que ejex: el orden es libre.
        correr(
            abrir_ventas()
            + "pinte barras ventas\n leyenda \"Totales\"\n ejey unidades\n"
            + ' titulo "Ventas por ciudad"\n ejex ciudad\n'
            + 'guardela "{0}"\nchao\n'.format(con_titulo)
        )
        png_sin = verificar_png_en_disco(sin_titulo)
        png_con = verificar_png_en_disco(con_titulo)
        assert png_sin != png_con, (
            "el título y la leyenda deben cambiar los píxeles del PNG"
        )
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@caso
def runtime_grafica_sin_clausula_final_no_escribe_archivo():
    carpeta = tempfile.mkdtemp(prefix="arepa_pinte_")
    anterior = os.getcwd()
    try:
        os.chdir(carpeta)
        programa = (
            abrir_ventas()
            + "pinte lineas ventas\n ejex fecha\n ejey unidades\nchao\n"
        )
        ejecutor = correr(programa)
        assert os.listdir(carpeta) == [], (
            "sin cláusula final no debe escribirse ningún archivo: {0}".format(
                os.listdir(carpeta)
            )
        )
        texto = "\n".join(ejecutor.contexto.salida)
        assert "lista" in texto and "guardela" in texto, (
            "el mensaje debe sugerir guardar o mostrar: {0}".format(texto)
        )
        assert ejecutor.contexto.archivos_generados == [], (
            "no debe registrarse un archivo sin cláusula final"
        )
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------------- #
# Caso de estudio final: programa.arepa y salidas versionables
# ---------------------------------------------------------------------- #

RUTA_CASO = os.path.join(RAIZ, "caso_estudio", "programa.arepa")
SALIDAS_CASO = os.path.join(RAIZ, "caso_estudio", "salidas")
PNG_CASO = (
    "01_serie.png",
    "02_barras.png",
    "03_histograma.png",
    "04_dispersion.png",
    "05_cajas.png",
)
CSV_CASO = os.path.join(SALIDAS_CASO, "pasajeros_por_anio.csv")


def ejecutar_caso_estudio():
    """Corre programa.arepa desde la raíz con AREPA_SIN_VENTANA=1."""
    entorno = dict(os.environ)
    entorno["AREPA_SIN_VENTANA"] = "1"
    entorno["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [
            sys.executable,
            os.path.join("src", "cli", "main.py"),
            os.path.join("caso_estudio", "programa.arepa"),
            "--ejecutar",
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=entorno,
        timeout=180,
    )


def hashes_salidas_caso():
    """SHA-256 de los seis archivos que produce el caso de estudio."""
    rutas = list(PNG_CASO) + ["pasajeros_por_anio.csv"]
    hashes = {}
    for nombre in rutas:
        ruta = os.path.join(SALIDAS_CASO, nombre)
        with open(ruta, "rb") as archivo:
            hashes[nombre] = hashlib.sha256(archivo.read()).hexdigest()
    return hashes


@caso
def caso_estudio_ejecuta_desde_la_raiz_sin_errores():
    resultado = ejecutar_caso_estudio()
    salida = (resultado.stdout or "") + (resultado.stderr or "")
    assert resultado.returncode == 0, (
        "el caso de estudio terminó con código {0}: {1}".format(
            resultado.returncode, salida[-2000:]
        )
    )
    assert "Error" not in salida, (
        "la salida del caso de estudio menciona un error: {0}".format(
            salida[-2000:]
        )
    )
    assert "¡De una! El programa corrió completo sin tropiezos." in salida, (
        "no aparece el mensaje final de ejecución correcta"
    )


@caso
def caso_estudio_genera_cinco_png_y_el_csv_anual():
    resultado = ejecutar_caso_estudio()
    assert resultado.returncode == 0, (
        "el caso de estudio no terminó limpio: {0}".format(resultado.stderr)
    )
    for nombre in PNG_CASO:
        verificar_png_en_disco(os.path.join(SALIDAS_CASO, nombre))

    assert os.path.isfile(CSV_CASO), "no se generó el resumen anual"
    with open(CSV_CASO, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    assert len(filas) == 12, (
        "el resumen anual debe tener 12 filas y tiene {0}".format(len(filas))
    )
    assert list(filas[0].keys()) == [
        "anio", "total", "promedio", "maximo_mes", "registros"
    ], "encabezado inesperado: {0}".format(list(filas[0].keys()))
    totales = {int(fila["anio"]): int(fila["total"]) for fila in filas}
    assert sorted(totales) == list(range(1949, 1961)), (
        "los años del resumen no van de 1949 a 1960: {0}".format(sorted(totales))
    )
    assert totales[1949] == 1520, "el total de 1949 debe ser 1520"
    assert totales[1960] == 5714, "el total de 1960 debe ser 5714"


@caso
def caso_estudio_imprime_los_indicadores_clave():
    resultado = ejecutar_caso_estudio()
    assert resultado.returncode == 0, "el caso de estudio no terminó limpio"
    salida = resultado.stdout or ""
    esperados = (
        "Registros limpios: 144",
        "Total pasajeros: 40363",
        "Promedio mensual: 280.2986111111111",
        "Mediana mensual: 265.5",
        "Minimo mensual: 104",
        "Maximo mensual: 622",
        "Total 1949: 1520",
        "Total 1960: 5714",
        "Crecimiento 1949-1960 (%): 275.92105263157896",
    )
    for linea in esperados:
        assert linea in salida, (
            "falta el indicador {0!r} en la salida: {1}".format(linea, salida)
        )


@caso
def caso_estudio_es_idempotente_y_determinista():
    primera = ejecutar_caso_estudio()
    assert primera.returncode == 0, "la primera ejecución falló"
    hashes_primera = hashes_salidas_caso()

    segunda = ejecutar_caso_estudio()
    assert segunda.returncode == 0, "la segunda ejecución falló"
    hashes_segunda = hashes_salidas_caso()

    assert hashes_primera == hashes_segunda, (
        "las salidas cambiaron entre dos ejecuciones: {0} != {1}".format(
            hashes_primera, hashes_segunda
        )
    )


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DEL ESCRITOR PNG PROPIO")
    print("=" * 78)
    for funcion in CASOS:
        try:
            funcion()
            pasaron += 1
            print("[PASÓ ] {0}".format(funcion.__name__))
        except AssertionError as problema:
            fallaron += 1
            print("[FALLÓ] {0}: {1}".format(funcion.__name__, problema))
        except Exception as problema:
            fallaron += 1
            print("[FALLÓ] {0}: excepción {1}".format(funcion.__name__, problema))
    print("-" * 78)
    print("Resultado: {0} de {1} pasaron".format(pasaron, len(CASOS)))
    return 0 if fallaron == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
