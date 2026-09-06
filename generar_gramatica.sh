#!/usr/bin/env bash
# ============================================================
#  AREPA - Regenera el lexer y el parser desde la gramatica (Linux)
#  Requiere: Java 11+, Python 3.11+ y antlr-4.13.2-complete.jar
#  Si tiene antlr4-tools instalado (python3 -m pip install antlr4-tools),
#  puede ejecutar directamente:
#     antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
# ============================================================
set -euo pipefail

# 1. Java debe existir en el PATH
if ! command -v java >/dev/null 2>&1; then
    echo "Error: no encontre 'java' en el PATH. Instale Java 11 o superior."
    exit 1
fi

# 2. La version de Java debe ser 11 o superior
VERSION_JAVA=$(java -version 2>&1 | head -n 1)
if [[ "$VERSION_JAVA" =~ \"([0-9]+) ]]; then
    MAYOR="${BASH_REMATCH[1]}"
    # Java 8 y anteriores usan esquema 1.x; Java 9+ usa el numero mayor directamente
    if [[ "$MAYOR" == "1" ]]; then
        echo "Error: se requiere Java 11 o superior (encontrado: $VERSION_JAVA)."
        exit 1
    elif (( MAYOR < 11 )); then
        echo "Error: se requiere Java 11 o superior (encontrado: $VERSION_JAVA)."
        exit 1
    fi
else
    echo "Advertencia: no pude determinar la version de Java ($VERSION_JAVA); continuo."
fi

# 3. ANTLR se detecta con ANTLR_JAR o con la ruta Linux por defecto
ANTLR_JAR="${ANTLR_JAR:-$HOME/antlr/antlr-4.13.2-complete.jar}"
if [[ ! -f "$ANTLR_JAR" ]]; then
    echo "Error: no encontre el jar de ANTLR en \"$ANTLR_JAR\"."
    echo "Descarguelo de https://www.antlr.org/download.html y guardelo ahi,"
    echo "o defina la variable ANTLR_JAR, por ejemplo:"
    echo "  export ANTLR_JAR=\"\$HOME/antlr/antlr-4.13.2-complete.jar\""
    exit 1
fi

# 4. La gramatica fuente debe existir
if [[ ! -f "gramatica/Arepa.g4" ]]; then
    echo "Error: no encontre gramatica/Arepa.g4. Ejecute desde la raiz del proyecto."
    exit 1
fi

# 5. El directorio de salida debe existir o poder crearse
mkdir -p generado

# 6. Generacion con ANTLR 4.13.2 (Python3, visitor, sin listener)
java -jar "$ANTLR_JAR" -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4

# 7. Verificar que la generacion termino correctamente
for archivo in generado/ArepaLexer.py generado/ArepaParser.py generado/ArepaVisitor.py; do
    if [[ ! -f "$archivo" ]]; then
        echo "Error: la generacion fallo, falta $archivo."
        exit 1
    fi
done

echo "Listo: codigo generado en generado/ (ArepaLexer.py, ArepaParser.py, ArepaVisitor.py)."
