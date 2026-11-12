"""
AREPA - Matemática propia (src/utiles/matematica.py)
----------------------------------------------------
Implementada por el equipo para que el motor gráfico y el resto de la
biblioteca no dependan del módulo 'math'. Solo usa aritmética básica de
Python (+, -, *, /, //, **) y comparaciones.

Qué ofrece:
  * es_finito(x)          -> ¿x es un número real (ni infinito ni NaN)?
  * piso(x) / techo(x)    -> mayor entero <= x / menor entero >= x
  * raiz_entera(n)        -> parte entera de la raíz cuadrada (Newton entero)
  * raiz_cuadrada(x)      -> raíz cuadrada real (Newton-Raphson)
  * exponente_decimal(x)  -> k tal que 10^k <= x < 10^(k+1)  (= piso(log10 x))

Decisiones propias documentadas:
  * es_finito usa que 'x - x' vale 0 solo para números finitos: para
    infinito y NaN esa resta da NaN, y NaN nunca es igual a nada;
  * piso y techo parten de int(x), que trunca hacia cero, y corrigen el
    lado negativo/positivo con una comparación;
  * raiz_entera trabaja solo con enteros, así no pierde precisión con
    números grandes (lo usa el círculo relleno del lienzo);
  * exponente_decimal no calcula un logaritmo: busca la potencia de 10
    que encierra a x comparando con 10.0 ** k, que es exacto para los
    tamaños de eje que maneja una gráfica.
"""

INFINITO = float("inf")


def es_finito(numero):
    """True si 'numero' no es infinito ni NaN."""
    try:
        return (numero - numero) == 0
    except (TypeError, OverflowError):
        return False


def piso(numero):
    """Mayor entero menor o igual que 'numero' (equivale a floor)."""
    if not es_finito(numero):
        raise ValueError("no se puede calcular el piso de un valor no finito.")
    entero = int(numero)
    if numero < entero:
        return entero - 1
    return entero


def techo(numero):
    """Menor entero mayor o igual que 'numero' (equivale a ceil)."""
    if not es_finito(numero):
        raise ValueError("no se puede calcular el techo de un valor no finito.")
    entero = int(numero)
    if numero > entero:
        return entero + 1
    return entero


def raiz_entera(numero):
    """Parte entera de la raíz cuadrada de un entero no negativo.

    Método de Newton sobre enteros: se parte de una estimación por encima
    y se promedia con numero // estimación hasta que deja de bajar.
    """
    if isinstance(numero, bool) or not isinstance(numero, int):
        raise ValueError("'numero' debe ser un entero.")
    if numero < 0:
        raise ValueError("no existe raíz cuadrada real de un negativo.")
    if numero < 2:
        return numero
    estimacion = 1 << ((numero.bit_length() + 1) // 2)
    while True:
        siguiente = (estimacion + numero // estimacion) // 2
        if siguiente >= estimacion:
            return estimacion
        estimacion = siguiente


def raiz_cuadrada(numero):
    """Raíz cuadrada real por Newton-Raphson (x = (x + n/x) / 2)."""
    numero = float(numero)
    if numero < 0 or numero != numero:
        raise ValueError("no existe raíz cuadrada real de un negativo.")
    if numero == 0 or numero == INFINITO:
        return numero
    estimacion = numero if numero >= 1 else 1.0
    for _ in range(200):
        siguiente = (estimacion + numero / estimacion) / 2.0
        if siguiente == estimacion:
            break
        estimacion = siguiente
    return estimacion


def exponente_decimal(numero):
    """Devuelve k entero con 10^k <= numero < 10^(k+1) (numero > 0)."""
    numero = float(numero)
    if not es_finito(numero) or numero <= 0:
        raise ValueError("el exponente decimal exige un número positivo finito.")
    exponente = 0
    while 10.0 ** (exponente + 1) <= numero:
        exponente += 1
    while 10.0 ** exponente > numero:
        exponente -= 1
    return exponente
