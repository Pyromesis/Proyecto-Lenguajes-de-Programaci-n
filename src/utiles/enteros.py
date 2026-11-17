"""Conversión decimal propia sin cambiar límites globales del intérprete.

Python limita int(texto) y str(entero) para decimales largos. AREPA procesa
bloques de nueve dígitos: cada conversión nativa queda por debajo del límite.
"""


def entero_a_texto(numero):
    if numero == 0:
        return "0"
    signo = "-" if numero < 0 else ""
    numero = abs(numero)
    bloques = []
    while numero:
        numero, resto = divmod(numero, 1000000000)
        bloques.append(resto)
    return signo + str(bloques[-1]) + "".join(
        str(bloque).rjust(9, "0") for bloque in reversed(bloques[:-1]))


def texto_a_entero(texto):
    texto = texto.strip()
    negativo = texto.startswith("-")
    digitos = texto[1:] if texto.startswith(("+", "-")) else texto
    if not digitos or not digitos.isdecimal():
        raise ValueError("El texto no representa un entero decimal.")
    numero = 0
    for inicio in range(0, len(digitos), 9):
        bloque = digitos[inicio:inicio + 9]
        numero = numero * (10 ** len(bloque)) + int(bloque)
    return -numero if negativo else numero
