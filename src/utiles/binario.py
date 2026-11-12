"""
AREPA - Empaquetado binario propio (src/utiles/binario.py)
----------------------------------------------------------
Implementado por el equipo para no depender de 'struct'. Convierte
enteros a bytes y de vuelta con desplazamientos y máscaras de bits.

  * entero_a_bytes(valor, cantidad, orden) -> bytes
  * bytes_a_entero(datos, orden)           -> int

'orden' es "grande" (big-endian: el byte más significativo va primero,
como exige PNG) o "pequeno" (little-endian, como exige DEFLATE).
"""

GRANDE = "grande"
PEQUENO = "pequeno"


def entero_a_bytes(valor, cantidad, orden=GRANDE):
    """Escribe 'valor' (entero sin signo) en 'cantidad' bytes."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError("'valor' debe ser un entero.")
    if valor < 0 or valor >= (1 << (8 * cantidad)):
        raise ValueError(
            "el valor {0} no cabe en {1} byte(s).".format(valor, cantidad)
        )
    partes = []
    for posicion in range(cantidad):
        # del byte menos significativo al más significativo
        partes.append((valor >> (8 * posicion)) & 0xFF)
    if orden == GRANDE:
        partes.reverse()
    elif orden != PEQUENO:
        raise ValueError("'orden' debe ser 'grande' o 'pequeno'.")
    return bytes(partes)


def bytes_a_entero(datos, orden=GRANDE):
    """Lee un entero sin signo desde 'datos'."""
    if orden == GRANDE:
        secuencia = datos
    elif orden == PEQUENO:
        secuencia = datos[::-1]
    else:
        raise ValueError("'orden' debe ser 'grande' o 'pequeno'.")
    valor = 0
    for byte in secuencia:
        valor = (valor << 8) | byte
    return valor
