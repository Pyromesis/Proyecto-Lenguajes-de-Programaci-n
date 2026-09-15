#!/usr/bin/env bash
# ============================================================
#  AREPA - Demo de sustentación (Cortes 1 y 2, Linux)
#  Ejecuta, en orden, la evidencia de docs/07_guia_sustentacion.md
#  y falla si algún paso no da lo esperado.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "### 1. Versiones"
python3 --version
java -version

echo "### 2. Dependencias"
python3 -m pip install -r requirements.txt

echo "### 3. Sincronía EBNF <-> ANTLR (46/46 reglas, 59 reservadas)"
python3 herramientas/chequeo_gramatica.py | grep -q "Sincronizado: 46/46"

echo "### 4. Programa válido (demo, 9 sentencias)"
python3 src/cli/main.py ejemplos/demo.arepa | grep -q "bien escrito"

echo "### 5. Tokens y árbol"
python3 src/cli/main.py ejemplos/demo.arepa --tokens | grep -q "QUIHUBO"
python3 src/cli/main.py ejemplos/demo.arepa --arbol | grep -q "Árbol de análisis"

echo "### 6. Programa inválido (código 1, con línea y columna)"
if python3 src/cli/main.py pruebas/negativos/n01_falta_chao.arepa; then
  echo "ERROR: el programa inválido debió fallar"
  exit 1
fi
# Se captura en variable (no en tubería) porque el exit 1 del programa
# es lo esperado y pipefail lo propagaría como fallo del paso.
texto=$(python3 src/cli/main.py pruebas/negativos/n01_falta_chao.arepa 2>&1 || true)
echo "$texto" | grep -q "Línea" || {
  echo "ERROR: falta línea y columna en el diagnóstico"
  exit 1
}

echo "### 7. Ejecución con datos reales + exportación CSV"
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar | grep -q "resumen_ciudades.csv"
test -f salidas/resumen_ciudades.csv

echo "### 8. Ciclos (ampliación Corte 2)"
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar | grep -q "factorial de 5: 120"
test -f salidas/resumen_ciclos.csv

echo "### 8b. Tercer programa completo con exportación (filtros)"
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar | grep -q "filtros_listos.csv"
test -f salidas/filtros_listos.csv

echo "### 9. Suite completa (6/6)"
python3 pruebas/test_proyecto.py 2>&1 | grep -q "6 de 6 suites pasaron"

echo "De una: demo de sustentación completa sin tropiezos."
