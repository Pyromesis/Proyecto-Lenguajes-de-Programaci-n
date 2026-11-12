"""
AREPA - SHA-256 propio (src/utiles/sha256.py)
---------------------------------------------
Implementación del algoritmo SHA-256 (FIPS 180-4) hecha por el equipo
para no depender de 'hashlib'. La usa herramientas/partir_datos.py para
repartir filas entre entrenamiento y prueba de forma reproducible.

Las constantes no se copian de una tabla: se calculan como indica el
estándar, a partir de las partes fraccionarias de la raíz cuadrada
(valores iniciales) y de la raíz cúbica (constantes K) de los primeros
números primos, usando solo aritmética entera.
"""

_MASCARA = 0xFFFFFFFF


def _primeros_primos(cantidad):
    primos = []
    candidato = 2
    while len(primos) < cantidad:
        es_primo = True
        for primo in primos:
            if primo * primo > candidato:
                break
            if candidato % primo == 0:
                es_primo = False
                break
        if es_primo:
            primos.append(candidato)
        candidato += 1
    return primos


def _raiz_entera(numero, indice):
    """Mayor entero r con r**indice <= numero (búsqueda binaria)."""
    bajo, alto = 0, 1
    while alto ** indice <= numero:
        alto *= 2
    while bajo < alto - 1:
        medio = (bajo + alto) // 2
        if medio ** indice <= numero:
            bajo = medio
        else:
            alto = medio
    return bajo


def _fraccion_raiz(primo, indice):
    """Primeros 32 bits de la parte fraccionaria de la raíz 'indice' de primo."""
    return _raiz_entera(primo << (32 * indice), indice) & _MASCARA


_PRIMOS = _primeros_primos(64)
_INICIALES = [_fraccion_raiz(p, 2) for p in _PRIMOS[:8]]
_K = [_fraccion_raiz(p, 3) for p in _PRIMOS]


def _rotar(valor, bits):
    """Rotación circular a la derecha de un entero de 32 bits."""
    return ((valor >> bits) | (valor << (32 - bits))) & _MASCARA


def sha256_hex(datos):
    """Devuelve el resumen SHA-256 de 'datos' (bytes) en hexadecimal."""
    mensaje = bytearray(datos)
    longitud_bits = len(mensaje) * 8
    mensaje.append(0x80)
    while len(mensaje) % 64 != 56:
        mensaje.append(0)
    for desplazamiento in range(56, -1, -8):
        mensaje.append((longitud_bits >> desplazamiento) & 0xFF)

    estado = list(_INICIALES)
    for inicio in range(0, len(mensaje), 64):
        w = []
        for i in range(16):
            j = inicio + 4 * i
            w.append(
                (mensaje[j] << 24) | (mensaje[j + 1] << 16)
                | (mensaje[j + 2] << 8) | mensaje[j + 3]
            )
        for i in range(16, 64):
            s0 = _rotar(w[i - 15], 7) ^ _rotar(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = _rotar(w[i - 2], 17) ^ _rotar(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & _MASCARA)

        a, b, c, d, e, f, g, h = estado
        for i in range(64):
            s1 = _rotar(e, 6) ^ _rotar(e, 11) ^ _rotar(e, 25)
            eleccion = (e & f) ^ ((~e & _MASCARA) & g)
            temporal1 = (h + s1 + eleccion + _K[i] + w[i]) & _MASCARA
            s0 = _rotar(a, 2) ^ _rotar(a, 13) ^ _rotar(a, 22)
            mayoria = (a & b) ^ (a & c) ^ (b & c)
            temporal2 = (s0 + mayoria) & _MASCARA
            h, g, f = g, f, e
            e = (d + temporal1) & _MASCARA
            d, c, b = c, b, a
            a = (temporal1 + temporal2) & _MASCARA

        nuevos = (a, b, c, d, e, f, g, h)
        estado = [(estado[i] + nuevos[i]) & _MASCARA for i in range(8)]

    return "".join("{0:08x}".format(parte) for parte in estado)
