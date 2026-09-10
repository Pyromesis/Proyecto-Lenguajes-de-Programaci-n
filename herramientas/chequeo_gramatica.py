"""
AREPA - Chequeo de sincronía gramática EBNF <-> ANTLR4 (herramientas/chequeo_gramatica.py)
----------------------------------------------------------------------------------------
Verifica que la especificación formal (`docs/03_gramatica_ebnf.md`) y la
implementación (`gramatica/Arepa.g4`) definan exactamente lo mismo:

  1. toda regla del `.g4` tiene su `<regla>` en la EBNF y viceversa;
  2. todo literal de palabra reservada del `.g4` aparece en la lista
     PALABRA_RESERVADA de la EBNF.

Uso:
    python herramientas/chequeo_gramatica.py

Salida: 0 si todo está sincronizado, 1 con el detalle si algo falta.
"""

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def reglas_g4(texto):
    """Nombres de reglas del .g4: líneas con un solo identificador minúsculo."""
    return [
        linea.strip()
        for linea in texto.splitlines()
        if re.match(r"^[a-z_]+$", linea.strip() or " ")
    ]


def main():
    with open(os.path.join(RAIZ, "gramatica", "Arepa.g4"), encoding="utf-8") as fh:
        g4 = fh.read()
    with open(os.path.join(RAIZ, "docs", "03_gramatica_ebnf.md"), encoding="utf-8") as fh:
        ebnf = fh.read()

    reglas = reglas_g4(g4)
    no_terminales = set(re.findall(r"<([a-z_]+)>", ebnf))
    literales = set(re.findall(r": '([a-z_]+)'", g4))

    fallos = []
    for regla in reglas:
        if regla not in no_terminales:
            fallos.append("la regla '{0}' del .g4 no está en la EBNF".format(regla))
    for nt in sorted(no_terminales):
        if nt not in reglas:
            fallos.append("el no terminal '<{0}>' de la EBNF no está en el .g4".format(nt))
    for lit in sorted(literales):
        if '"{0}"'.format(lit) not in ebnf and lit not in ebnf:
            fallos.append("la reservada '{0}' del .g4 no está en la EBNF".format(lit))

    print("Reglas del .g4: {0} | no terminales EBNF: {1} | reservadas: {2}".format(
        len(reglas), len(no_terminales), len(literales)))
    if fallos:
        print("DESINCRONIZADO ({0}):".format(len(fallos)))
        for f in fallos:
            print("  - " + f)
        return 1
    print("Sincronizado: {0}/{0} reglas y {1} reservadas.".format(len(reglas), len(literales)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
