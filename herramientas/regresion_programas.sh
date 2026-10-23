#!/usr/bin/env bash
# ============================================================
#  AREPA - Regresión de todos los programas
#  Ejecuta los .arepa de ejercicios/ (164) y ejemplos/ (6) con --ejecutar.
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
ejemplos=$(find ejemplos -name '*.arepa' -type f | wc -l)
if [ "$c1" -ne 32 ] || [ "$c2" -ne 120 ] || [ "$c3" -ne 12 ] || [ "$ejemplos" -ne 6 ]; then
  echo "Conteo inesperado: C1=$c1 (32), C2=$c2 (120), C3=$c3 (12), ejemplos=$ejemplos (6)."
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
done < <(find ejercicios ejemplos -name '*.arepa' -type f | sort)

if [ "$total" -ne 170 ]; then
  echo "Conteo total inesperado: ${total} programas (esperados 170: 164 ejercicios + 6 ejemplos)."
  exit 1
fi

if [ "$fallos" -ne 0 ]; then
  printf '\nEjercicios con fallo:%b\n' "$detalle"
  echo "Regresión: ${fallos} de ${total} fallaron."
  exit 1
fi

echo "Regresión de programas: ${total} programas, 0 fallos."
