"""
AREPA - Texto propio (src/utiles/texto.py)
------------------------------------------
Implementado por el equipo para no depender de 're' ni de 'unicodedata'.

Qué ofrece:
  * es_identificador(texto)  -> ¿es un nombre válido? (letra o '_' y luego
                                letras, dígitos o '_'; acepta tildes y ñ)
  * colapsar_espacios(texto) -> une cualquier racha de blancos en un espacio
  * quitar_tildes(texto)     -> á -> a, ñ -> n, ü -> u ... con tabla propia

Decisiones propias documentadas:
  * es_identificador reproduce la regla ID de la gramática (Arepa.g4)
    recorriendo carácter por carácter, sin expresiones regulares;
  * quitar_tildes usa una tabla propia letra base -> variantes
    acentuadas (latín occidental y extendido); lo que no esté en la tabla
    se devuelve igual y la fuente bitmap decide cómo dibujarlo;
  * las marcas combinantes sueltas (U+0300..U+036F), que aparecen cuando
    un texto ya viene descompuesto, se descartan.
"""

# Letra base ASCII -> todas sus variantes con tilde, diéresis, virgulilla, etc.
_VARIANTES = {
    "A": "ÀÁÂÃÄÅĀĂĄǍǞǠǺȀȂȦḀẠẢẤẦẨẪẬẮẰẲẴẶ",
    "B": "ḂḄḆ",
    "C": "ÇĆĈĊČḈ",
    "D": "ĎḊḌḎḐḒ",
    "E": "ÈÉÊËĒĔĖĘĚȄȆȨḔḖḘḚḜẸẺẼẾỀỂỄỆ",
    "F": "Ḟ",
    "G": "ĜĞĠĢǦǴḠ",
    "H": "ĤȞḢḤḦḨḪ",
    "I": "ÌÍÎÏĨĪĬĮİǏȈȊḬḮỈỊ",
    "J": "Ĵ",
    "K": "ĶǨḰḲḴ",
    "L": "ĹĻĽḶḸḺḼ",
    "M": "ḾṀṂ",
    "N": "ÑŃŅŇǸṄṆṈṊ",
    "O": "ÒÓÔÕÖŌŎŐƠǑǪǬȌȎȪȬȮȰṌṎṐṒỌỎỐỒỔỖỘỚỜỞỠỢ",
    "P": "ṔṖ",
    "R": "ŔŖŘȐȒṘṚṜṞ",
    "S": "ŚŜŞŠȘṠṢṤṦṨ",
    "T": "ŢŤȚṪṬṮṰ",
    "U": "ÙÚÛÜŨŪŬŮŰŲƯǓǕǗǙǛȔȖṲṴṶṸṺỤỦỨỪỬỮỰ",
    "V": "ṼṾ",
    "W": "ŴẀẂẄẆẈ",
    "X": "ẊẌ",
    "Y": "ÝŶŸȲẎỲỴỶỸ",
    "Z": "ŹŻŽẐẒẔ",
    "a": "àáâãäåāăąǎǟǡǻȁȃȧḁạảấầẩẫậắằẳẵặ",
    "b": "ḃḅḇ",
    "c": "çćĉċčḉ",
    "d": "ďḋḍḏḑḓ",
    "e": "èéêëēĕėęěȅȇȩḕḗḙḛḝẹẻẽếềểễệ",
    "f": "ḟ",
    "g": "ĝğġģǧǵḡ",
    "h": "ĥȟḣḥḧḩḫẖ",
    "i": "ìíîïĩīĭįǐȉȋḭḯỉị",
    "j": "ĵǰ",
    "k": "ķǩḱḳḵ",
    "l": "ĺļľḷḹḻḽ",
    "m": "ḿṁṃ",
    "n": "ñńņňǹṅṇṉṋ",
    "o": "òóôõöōŏőơǒǫǭȍȏȫȭȯȱṍṏṑṓọỏốồổỗộớờởỡợ",
    "p": "ṕṗ",
    "r": "ŕŗřȑȓṙṛṝṟ",
    "s": "śŝşšșṡṣṥṧṩ",
    "t": "ţťțṫṭṯṱẗ",
    "u": "ùúûüũūŭůűųưǔǖǘǚǜȕȗṳṵṷṹṻụủứừửữự",
    "v": "ṽṿ",
    "w": "ŵẁẃẅẇẉẘ",
    "x": "ẋẍ",
    "y": "ýÿŷȳẏẙỳỵỷỹ",
    "z": "źżžẑẓẕ",
}

_SIN_TILDE = {}
for _base, _variantes in _VARIANTES.items():
    for _letra in _variantes:
        _SIN_TILDE[_letra] = _base

_COMBINANTE_MIN = 0x0300
_COMBINANTE_MAX = 0x036F


def es_identificador(texto):
    """True si 'texto' es un identificador válido de AREPA."""
    if not isinstance(texto, str) or texto == "":
        return False
    primero = texto[0]
    if not (primero == "_" or primero.isalpha()):
        return False
    for caracter in texto[1:]:
        if not (caracter == "_" or caracter.isalnum()):
            return False
    return True


def colapsar_espacios(texto):
    """Reemplaza cada racha de blancos por un solo espacio y recorta."""
    palabras = []
    actual = []
    for caracter in texto:
        if caracter.isspace():
            if actual:
                palabras.append("".join(actual))
                actual = []
        else:
            actual.append(caracter)
    if actual:
        palabras.append("".join(actual))
    return " ".join(palabras)


def quitar_tildes(texto):
    """Devuelve 'texto' con cada letra acentuada cambiada por su base."""
    salida = []
    for caracter in texto:
        codigo = ord(caracter)
        if _COMBINANTE_MIN <= codigo <= _COMBINANTE_MAX:
            continue  # tilde suelta de un texto ya descompuesto
        salida.append(_SIN_TILDE.get(caracter, caracter))
    return "".join(salida)
