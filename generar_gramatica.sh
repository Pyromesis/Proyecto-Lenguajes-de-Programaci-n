#!/usr/bin/env bash
# ============================================================
#  AREPA - Regenera el lexer y el parser desde la gramatica
#  Requiere: Java 11+ y antlr-4.13.2-complete.jar
#  Si tiene antlr4-tools instalado (pip install antlr4-tools),
#  puede ejecutar directamente:
#     antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
# ============================================================
set -euo pipefail

JAR="${ANTLR_JAR:-$HOME/antlr/antlr-4.13.2-complete.jar}"

if [ ! -f "$JAR" ]; then
    echo "No encontre el jar de ANTLR en \"$JAR\"."
    echo "Descarguelo de https://www.antlr.org/download.html o defina ANTLR_JAR."
    exit 1
fi

if ! command -v java >/dev/null 2>&1; then
    echo "No encontre 'java' en el PATH. Instale Java 11+."
    exit 1
fi

java -jar "$JAR" -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4

echo "Listo: codigo generado en generado/"
