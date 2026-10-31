#!/usr/bin/env python3
"""AREPA - Chequeo estructural de la gramática EBNF <-> ANTLR4.

Este verificador no se limita a comparar nombres: traduce cada producción
del `.g4` y de `docs/03_gramatica_ebnf.md` a un árbol canónico y exige que
coincidan las alternativas, su orden, las secuencias, los opcionales, las
repeticiones y los terminales. También comprueba:

  * que las 64 reglas del parser existan en ambos archivos;
  * que la lista ordenada de la sección 10 coincida con el `.g4`;
  * que `PALABRA_RESERVADA` tenga exactamente los 79 literales del lexer;
  * que `nombre_columna` cubra ID y todas las palabras reservadas.

La única comparación no estrictamente ordenada es `nombre_columna`, porque
el orden de sus alternativas (todas palabras reservadas) no cambia el
lenguaje; se compara como conjunto para no imponer un orden artificial.

Uso:
    python3 herramientas/chequeo_gramatica.py

Salida: 0 si todo está sincronizado, 1 con el detalle si algo difiere.
"""

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def limpiar_comentarios(texto):
    """Quita comentarios de bloque y de línea del `.g4`."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return re.sub(r"//[^\n]*", "", texto)


def reglas_g4(texto):
    """Devuelve [(nombre, cuerpo)] de todas las reglas del `.g4`."""
    texto = limpiar_comentarios(texto)
    return [
        (m.group(1), m.group(2).strip())
        for m in re.finditer(
            r"(?ms)^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?);", texto
        )
    ]


def producciones_ebnf(texto):
    """Extrae las producciones de los bloques ```ebnf del documento."""
    bloques = re.findall(r"```ebnf\s*\n(.*?)```", texto, re.S)
    producciones = []
    vistos = set()

    def guardar(actual):
        if actual and actual[0] not in vistos:
            producciones.append(actual)
            vistos.add(actual[0])

    for bloque in bloques:
        actual = None
        for linea in bloque.splitlines():
            m = re.match(
                r"^\s*(?:<([a-z_]+)>|([A-Z_]+))\s*::=\s*(.*)$", linea
            )
            if m:
                guardar(actual)
                nombre = m.group(1) or m.group(2)
                actual = [nombre, m.group(3).strip()]
            elif actual is not None:
                if linea.strip():
                    actual[1] += " " + linea.strip()
                else:
                    guardar(actual)
                    actual = None
        guardar(actual)
    return producciones


class ErrorGramatica(Exception):
    """Error de lectura o de estructura durante la comparación."""


def tokenizar_g4(cuerpo, literales):
    """Convierte un cuerpo ANTLR en tokens canónicos."""
    tokens = []
    i = 0
    while i < len(cuerpo):
        c = cuerpo[i]
        if c.isspace():
            i += 1
            continue
        if c == "'":
            j = i + 1
            valor = []
            while j < len(cuerpo):
                if cuerpo[j] == "\\" and j + 1 < len(cuerpo):
                    valor.append(cuerpo[j:j + 2])
                    j += 2
                    continue
                if cuerpo[j] == "'":
                    break
                valor.append(cuerpo[j])
                j += 1
            if j >= len(cuerpo):
                raise ErrorGramatica("literal sin cerrar en .g4")
            texto = "".join(valor)
            tokens.append(("T", literales.get(texto, "LIT:" + texto)))
            i = j + 1
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < len(cuerpo) and (cuerpo[j].isalnum() or cuerpo[j] == "_"):
                j += 1
            nombre = cuerpo[i:j]
            tokens.append(("T", nombre) if nombre.isupper() else ("R", nombre))
            i = j
            continue
        if c in "()|?*+;:,":
            tokens.append(("SYM", c))
            i += 1
            continue
        tokens.append(("SYM", c))
        i += 1
    return tokens


def tokenizar_ebnf(cuerpo, literales):
    """Convierte un cuerpo EBNF en los mismos tokens canónicos."""
    tokens = []
    i = 0
    while i < len(cuerpo):
        c = cuerpo[i]
        if c.isspace():
            i += 1
            continue
        if c == "<":
            j = cuerpo.find(">", i + 1)
            if j < 0:
                raise ErrorGramatica("no terminal sin cerrar en EBNF")
            tokens.append(("R", cuerpo[i + 1:j].strip()))
            i = j + 1
            continue
        if c == '"':
            j = i + 1
            valor = []
            while j < len(cuerpo):
                if cuerpo[j] == "\\" and j + 1 < len(cuerpo):
                    valor.append(cuerpo[j:j + 2])
                    j += 2
                    continue
                if cuerpo[j] == '"':
                    break
                valor.append(cuerpo[j])
                j += 1
            if j >= len(cuerpo):
                raise ErrorGramatica("literal sin cerrar en EBNF")
            texto = "".join(valor)
            if texto not in literales:
                raise ErrorGramatica(
                    "literal EBNF sin token en .g4: {0!r}".format(texto)
                )
            tokens.append(("T", literales[texto]))
            i = j + 1
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < len(cuerpo) and (cuerpo[j].isalnum() or cuerpo[j] == "_"):
                j += 1
            nombre = cuerpo[i:j]
            if nombre == "PALABRA_RESERVADA":
                tokens.append(("R", nombre))
            elif nombre.isupper():
                tokens.append(("T", nombre))
            else:
                tokens.append(("R", nombre))
            i = j
            continue
        if cuerpo.startswith("::=", i):
            tokens.append(("SYM", "::="))
            i += 3
            continue
        if c in "()[]{}|?*+;:,":
            tokens.append(("SYM", c))
            i += 1
            continue
        tokens.append(("SYM", c))
        i += 1
    return tokens


class Parser:
    """Parser descendente de la notación de gramáticas."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def ver(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def comer(self, esperado=None):
        actual = self.ver()
        if actual is None:
            raise ErrorGramatica("fin inesperado")
        if esperado is not None and actual != esperado:
            raise ErrorGramatica(
                "se esperaba {0}, llegó {1}".format(esperado, actual)
            )
        self.pos += 1
        return actual

    def alternativas(self):
        opciones = [self.secuencia()]
        while self.ver() == ("SYM", "|"):
            self.comer()
            opciones.append(self.secuencia())
        return opciones[0] if len(opciones) == 1 else ("alt", tuple(opciones))

    def secuencia(self):
        elementos = []
        while self.ver() is not None and self.ver() not in (
            ("SYM", "|"), ("SYM", ")"), ("SYM", "]"), ("SYM", "}")
        ):
            elementos.append(self.termino())
        if not elementos:
            return ("vacio",)
        return elementos[0] if len(elementos) == 1 else ("seq", tuple(elementos))

    def termino(self):
        base = self.factor()
        while self.ver() in (("SYM", "?"), ("SYM", "*"), ("SYM", "+")):
            op = self.comer()[1]
            base = ({"?": "opt", "*": "star", "+": "plus"}[op], base)
        return base

    def factor(self):
        actual = self.ver()
        if actual == ("SYM", "("):
            self.comer()
            interior = self.alternativas()
            self.comer(("SYM", ")"))
            return interior
        if actual == ("SYM", "["):
            self.comer()
            interior = self.alternativas()
            self.comer(("SYM", "]"))
            return ("opt", interior)
        if actual == ("SYM", "{"):
            self.comer()
            interior = self.alternativas()
            self.comer(("SYM", "}"))
            return ("star", interior)
        if actual is not None and actual[0] in ("T", "R"):
            return self.comer()
        raise ErrorGramatica("token inesperado: {0}".format(actual))


def normalizar(ast):
    """Iguala `[NL]` de la EBNF con `NL*` del `.g4`."""
    if ast[0] == "opt" and ast[1] == ("T", "NL"):
        return ("star", ("T", "NL"))
    if ast[0] in ("opt", "star", "plus"):
        return (ast[0], normalizar(ast[1]))
    if ast[0] == "seq":
        return ("seq", tuple(normalizar(x) for x in ast[1]))
    if ast[0] == "alt":
        return ("alt", tuple(normalizar(x) for x in ast[1]))
    return ast


def parsear(cuerpo, literales, es_ebnf):
    tokens = (
        tokenizar_ebnf(cuerpo, literales)
        if es_ebnf
        else tokenizar_g4(cuerpo, literales)
    )
    parser = Parser(tokens)
    ast = parser.alternativas()
    if parser.ver() is not None:
        raise ErrorGramatica("sobró {0}".format(parser.ver()))
    return normalizar(ast)


def alternativas_planas(ast):
    if ast[0] == "alt":
        salida = []
        for opcion in ast[1]:
            salida.extend(alternativas_planas(opcion))
        return salida
    return [ast]


def sustituir(ast, nombre, reemplazo):
    """Reemplaza una referencia (PALABRA_RESERVADA) por su expansión."""
    if ast[0] == "R" and ast[1] == nombre:
        return reemplazo
    if ast[0] in ("opt", "star", "plus"):
        return (ast[0], sustituir(ast[1], nombre, reemplazo))
    if ast[0] == "seq":
        return ("seq", tuple(sustituir(x, nombre, reemplazo) for x in ast[1]))
    if ast[0] == "alt":
        return ("alt", tuple(sustituir(x, nombre, reemplazo) for x in ast[1]))
    return ast


def main():
    with open(
        os.path.join(RAIZ, "gramatica", "Arepa.g4"), encoding="utf-8"
    ) as fh:
        g4 = fh.read()
    with open(
        os.path.join(RAIZ, "docs", "03_gramatica_ebnf.md"), encoding="utf-8"
    ) as fh:
        ebnf = fh.read()

    reglas = reglas_g4(g4)
    reglas_parser = [(n, c) for n, c in reglas if n.islower()]
    reglas_lexer = [(n, c) for n, c in reglas if n.isupper()]

    literales = {}
    for nombre, cuerpo in reglas_lexer:
        m = re.fullmatch(r"'([^']*)'", cuerpo.strip())
        if m:
            literales[m.group(1)] = nombre

    producciones = producciones_ebnf(ebnf)
    ebnf_map = dict(producciones)
    reservadas_ast = (
        parsear(ebnf_map["PALABRA_RESERVADA"], literales, True)
        if "PALABRA_RESERVADA" in ebnf_map
        else None
    )

    fallos = []
    for nombre, cuerpo in reglas_parser:
        if nombre not in ebnf_map:
            fallos.append("falta la regla '{0}' en la EBNF".format(nombre))
            continue
        try:
            produccion_g4 = parsear(cuerpo, literales, False)
            produccion_ebnf = parsear(ebnf_map[nombre], literales, True)
        except ErrorGramatica as exc:
            fallos.append("{0}: {1}".format(nombre, exc))
            continue
        if nombre == "nombre_columna":
            if reservadas_ast is None:
                fallos.append(
                    "falta PALABRA_RESERVADA para expandir nombre_columna"
                )
                continue
            produccion_ebnf = sustituir(
                produccion_ebnf, "PALABRA_RESERVADA", reservadas_ast
            )
            conjunto_g4 = set(alternativas_planas(produccion_g4))
            conjunto_ebnf = set(alternativas_planas(produccion_ebnf))
            if conjunto_g4 != conjunto_ebnf:
                fallos.append(
                    "nombre_columna: solo en .g4={0}; solo en EBNF={1}".format(
                        sorted(conjunto_g4 - conjunto_ebnf),
                        sorted(conjunto_ebnf - conjunto_g4),
                    )
                )
            continue
        if produccion_g4 != produccion_ebnf:
            fallos.append(
                "{0}: la producción no coincide\n  .g4 = {1}\n  EBNF= {2}".format(
                    nombre, produccion_g4, produccion_ebnf
                )
            )

    for nombre, _ in producciones:
        if (
            nombre != "PALABRA_RESERVADA"
            and nombre.islower()
            and nombre not in dict(reglas_parser)
        ):
            fallos.append("sobra la regla '{0}' en la EBNF".format(nombre))

    if reservadas_ast is None:
        fallos.append("falta PALABRA_RESERVADA en la EBNF")
    else:
        reservadas_ebnf = [
            x for x in alternativas_planas(reservadas_ast) if x[0] == "T"
        ]
        reservadas_g4 = {
            ("T", n)
            for texto, n in literales.items()
            if re.fullmatch(r"[a-z_]+", texto)
        }
        if set(reservadas_ebnf) != reservadas_g4:
            fallos.append(
                "PALABRA_RESERVADA no coincide con los literales del lexer"
            )
        if len(reservadas_ebnf) != len(set(reservadas_ebnf)):
            fallos.append("PALABRA_RESERVADA tiene literales repetidos")

    m = re.search(
        r"Los nombres\s+de las (\d+) reglas.*?:\s*\n\n(.*?)\n\n",
        ebnf,
        re.S,
    )
    if not m:
        fallos.append(
            "no encontré la lista ordenada de reglas en la sección 10"
        )
    else:
        nombres_doc = re.findall(r"`([a-z_]+)`", m.group(2))
        nombres_g4 = [n for n, _ in reglas_parser]
        if int(m.group(1)) != len(nombres_g4):
            fallos.append(
                "la sección 10 declara {0} reglas y el .g4 tiene {1}".format(
                    m.group(1), len(nombres_g4)
                )
            )
        if nombres_doc != nombres_g4:
            fallos.append(
                "el orden de la sección 10 no coincide con el .g4"
            )

    print(
        "Reglas del .g4: {0} | producciones EBNF: {1} | reservadas: {2}".format(
            len(reglas_parser),
            len([n for n, _ in producciones if n.islower()]),
            len(reservadas_ebnf) if reservadas_ast is not None else 0,
        )
    )
    if fallos:
        print("DESINCRONIZADO ({0}):".format(len(fallos)))
        for fallo in fallos:
            print("  - " + fallo)
        return 1
    print(
        "Sincronizado: {0}/{0} producciones equivalentes y {1} reservadas.".format(
            len(reglas_parser), len(reservadas_ebnf)
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
