#!/usr/bin/env bash
# ============================================================
#  AREPA - Demo de sustentación (Cortes 1, 2 y 3, Linux)
#  Ejecuta, en orden, la evidencia de docs/07_guia_sustentacion.md
#  y falla si algún paso no da lo esperado.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

# Intérprete de Python: respeta $PYTHON si el usuario lo define; si no,
# usa el del entorno virtual (.venv/bin/python, único que trae antlr4 aquí);
# y si no existe, cae a python3 del sistema.
if [ -z "${PYTHON:-}" ]; then
  if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
  else
    PYTHON="python3"
  fi
fi

echo "### 1. Versiones"
"$PYTHON" --version
java -version

echo "### 2. Dependencias"
"$PYTHON" -m pip install -r requirements.txt

echo "### 3. Sincronía EBNF <-> ANTLR (57/57 reglas, 65 reservadas)"
"$PYTHON" herramientas/chequeo_gramatica.py | grep -q "Sincronizado: 57/57"

echo "### 4. Programa válido (demo, 9 sentencias)"
"$PYTHON" src/cli/main.py ejemplos/demo.arepa | grep -q "bien escrito"

echo "### 5. Tokens y árbol"
# Se captura la salida antes de buscar: 'grep -q' cierra la tubería en
# cuanto encuentra el patrón y, con salidas largas, el CLI recibiría
# SIGPIPE/BrokenPipe (y 'pipefail' haría fallar el paso).
tokens=$("$PYTHON" src/cli/main.py ejemplos/demo.arepa --tokens)
printf '%s\n' "$tokens" | grep -q "QUIHUBO"
arbol=$("$PYTHON" src/cli/main.py ejemplos/demo.arepa --arbol)
printf '%s\n' "$arbol" | grep -q "Árbol de análisis"

echo "### 5b. Ayuda y versión del CLI"
"$PYTHON" src/cli/main.py --version | grep -q "AREPA v0.4"
"$PYTHON" src/cli/main.py --ayuda | grep -q -- "--sin-ventana"
"$PYTHON" src/cli/main.py --help | grep -q -- "--ejecutar"

echo "### 6. Programa inválido (código 1, con línea y columna)"
if "$PYTHON" src/cli/main.py pruebas/negativos/n01_falta_chao.arepa; then
  echo "ERROR: el programa inválido debió fallar"
  exit 1
fi
# Se captura en variable (no en tubería) porque el exit 1 del programa
# es lo esperado y pipefail lo propagaría como fallo del paso.
texto=$("$PYTHON" src/cli/main.py pruebas/negativos/n01_falta_chao.arepa 2>&1 || true)
echo "$texto" | grep -q "Línea" || {
  echo "ERROR: falta línea y columna en el diagnóstico"
  exit 1
}

echo "### 7. Ejecución con datos reales + exportación CSV"
"$PYTHON" src/cli/main.py ejemplos/demo.arepa --ejecutar | grep -q "resumen_ciudades.csv"
test -f salidas/resumen_ciudades.csv

echo "### 8. Ciclos (ampliación Corte 2)"
"$PYTHON" src/cli/main.py ejemplos/ciclos.arepa --ejecutar | grep -q "factorial de 5: 120"
test -f salidas/resumen_ciclos.csv

echo "### 8b. Tercer programa completo con exportación (filtros)"
"$PYTHON" src/cli/main.py ejemplos/filtros.arepa --ejecutar | grep -q "filtros_listos.csv"
test -f salidas/filtros_listos.csv

echo "### 8c. Estructuras en memoria (Corte 2)"
"$PYTHON" src/cli/main.py ejemplos/memoria.arepa --ejecutar | grep -q "Total: 550000"
test -f salidas/memoria_resumen.csv
grep -q "^Mercado,365000," salidas/memoria_resumen.csv

echo "### 8d. Caso de estudio (Fase 3): 5 PNG + CSV sin ventana"
caso=$("$PYTHON" src/cli/main.py caso_estudio/programa.arepa --ejecutar --sin-ventana)
echo "$caso" | grep -q "Total pasajeros: 40363"
test -f caso_estudio/salidas/pasajeros_por_anio.csv
for imagen in 01_serie 02_barras 03_histograma 04_dispersion 05_cajas; do
  test -f "caso_estudio/salidas/$imagen.png" || {
    echo "ERROR: falta caso_estudio/salidas/$imagen.png"
    exit 1
  }
done

echo "### 9. Suite completa (8/8)"
suite=$("$PYTHON" pruebas/test_proyecto.py 2>&1)
printf '%s\n' "$suite" | grep -q "8 de 8 suites pasaron"

echo "### 9b. Documentación y estructura"
"$PYTHON" herramientas/chequeo_documentacion.py | grep -q "0 rutas antiguas"

echo "De una: demo de sustentación completa sin tropiezos."
