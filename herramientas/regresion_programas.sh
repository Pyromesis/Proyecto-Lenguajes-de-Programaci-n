#!/usr/bin/env bash
# ============================================================
#  AREPA - Regresión de todos los programas
#  Ejecuta los .arepa de los cortes (349) y ejemplos/ (9) con --ejecutar.
#  Falla si alguno termina con código distinto de 0.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${PYTHON:-}" ]; then
  if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
  else
    PYTHON="python3"
  fi
fi

export AREPA_SIN_VENTANA=1
total=0
fallos=0
detalle=""

# Conteo canónico por corte: si cambia, actualizá estos valores y la
# documentación (README, docs/11 y docs/12).
c1=$(find ejercicios/corte1 -name '*.arepa' -type f | wc -l)
c2=$(find ejercicios/corte2 -name '*.arepa' -type f | wc -l)
c3=$(find ejercicios/corte3 -name '*.arepa' -type f | wc -l)
completo=$(find ejercicios/corte_completo -name '*.arepa' -type f | wc -l)
ejemplos=$(find ejemplos -name '*.arepa' -type f | wc -l)
if [ "$c1" -ne 75 ] || [ "$c2" -ne 150 ] || [ "$c3" -ne 87 ] || [ "$completo" -ne 37 ] || [ "$ejemplos" -ne 9 ]; then
  echo "Conteo inesperado: C1=$c1 (75), C2=$c2 (150), C3=$c3 (87), completo=$completo (37), ejemplos=$ejemplos (9)."
  exit 1
fi

log=$(mktemp)
trap 'rm -f "$log"' EXIT

while IFS= read -r archivo; do
  total=$((total + 1))
  if ! "$PYTHON" src/cli/main.py "$archivo" --ejecutar --sin-ventana >"$log" 2>&1; then
    fallos=$((fallos + 1))
    detalle="${detalle}\n- ${archivo}"
    echo "FALLÓ: ${archivo}"
    sed -n '1,12p' "$log"
  fi
done < <(find ejercicios/corte1 ejercicios/corte2 ejercicios/corte3 ejercicios/corte_completo ejemplos -name '*.arepa' -type f | sort)

if [ "$total" -ne 358 ]; then
  echo "Conteo total inesperado: ${total} programas (esperados 358: 349 ejercicios + 9 ejemplos)."
  exit 1
fi

if [ "$fallos" -ne 0 ]; then
  printf '\nEjercicios con fallo:%b\n' "$detalle"
  echo "Regresión: ${fallos} de ${total} fallaron."
  exit 1
fi

echo "Regresión de programas: ${total} programas, 0 fallos."
