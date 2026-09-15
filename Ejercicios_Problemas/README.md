# Ejercicios y problemas AREPA (Linux)

187 programas `.arepa` de práctica, todos validan
(`python3 src/cli/main.py <archivo>`) y ejecutan
(`--ejecutar`) desde la raíz del proyecto. Las rutas `datos/...`
se resuelven desde ahí.

```bash
# Correr uno
python3 src/cli/main.py Ejercicios_Problemas/faciles/F12_deje_donde_simple.arepa --ejecutar
```

Convenciones de nombre: `F` fácil, `M` mediano, `D` difícil, numerados
en orden (`F01–F26`, `M01–M25`, `D01–D26`). Cada archivo trae en sus
primeras líneas qué concepto del Corte ejercita. Los que usan `guarde`
escriben en `salidas/ej_*.csv` (temporal, ignorado por git).

## Corte 1 y repaso general

| Carpeta | Contenido |
|---|---|
| `faciles/F01–F11` | programa mínimo, asignaciones, literales, comentarios, operadores, lógicos, `cuenteme`/`describa`, `monte`, `escoja`, condicional, división |
| `medianos/M01–M10` | precedencia, pipeline+filtro, `acomode`, `limpie`, `cree`+`renombre`, `convierta`, `invente`, `sino`, `resuma`, `pinte` |
| `dificiles/D01–D11` | potencia/unarios, Unicode, `nada`, closures, estadísticas, merge sort, bisiestos, CSV con comillas, `guarde`, flujo completo, bordes |
| `datos/` | `vacia.csv`, `comillas.csv` (casos borde del lector propio) |

## Corte 2 — Semántica y procesamiento de datos (F12–F26, M11–M25, D12–D26)

| Fáciles (F12–F26) | Qué ejercita |
|---|---|
| F12 `deje donde` simple | filtrado con comparación sencilla |
| F13 `cree` calculada | columna `unidades * precio` |
| F14 `acomode` simple | orden descendente propio |
| F15 `renombre` | cambio de nombre de columna |
| F16 `convierta` a texto | conversión numero → texto |
| F17 `limpie` duplicados | primera aparición se conserva |
| F18 `limpie vacios con` | relleno de `nada` con 0 |
| F19 `guarde` CSV | escritor propio UTF-8 |
| F20 `cuente`/`sume` | `resuma` sin junte (una fila) |
| F21 `promedie`/`minimo`/`maximo` | agregaciones básicas |
| F22 `mediana`/`desviacion` | inserción propia y poblacional |
| F23 `junte` + `cuente` | agrupamiento por ciudad |
| F24 `describa` | resumen estadístico propio |
| F25 `mientras` contador | condición que se vuelve falsa |
| F26 `repita N veces` | ciclo contado |

| Medianos (M11–M25) | Qué ejercita |
|---|---|
| M11 pipeline triple | `escoja` + `deje` + `cree` |
| M12 filtro compuesto | `y`/`o` con paréntesis |
| M13 doble clave | `acomode` por 2 columnas |
| M14 `convierta` fecha | calendario propio AAAA-MM-DD |
| M15 vacíos eliminan filas | `limpie vacios` sin `con` |
| M16 junte doble | ciudad + categoría |
| M17 cuatro agregaciones | `sume`/`promedie`/`minimo`/`maximo` |
| M18 `mientras` + `pare` | parada temprana |
| M19 rango 1..100 | inclusivo (5050) |
| M20 rango descendente | paso -1 automático |
| M21 `sino` encadenado | clasificación |
| M22 `invente` en `cree` | función por fila |
| M23 `guarde` + relectura | roundtrip del escritor |
| M24 closure | función lee global |
| M25 `pinte` validada | tabla y columnas (Fase 3 el PNG) |

| Difíciles (D12–D26) | Qué ejercita |
|---|---|
| D12 `resuma` sin junte | un solo grupo |
| D13 agregaciones ignoran `nada` | ingreso vacío de la encuesta |
| D14 tabla vacía | `sume`/`promedie` → `nada`, `cuente` → 0 |
| D15 junte interrumpido | claves rezagadas se descartan |
| D16 mediana par/impar | 12 filas vs filtradas |
| D17 desviación por grupos | poblacional por ciudad |
| D18 paso + `pare` + `siga` | control fino del rango |
| D19 factorial iterativo | 6! = 720 con `mientras` |
| D20 factorial recursivo | caso base + closure |
| D21 flujo ventas + `guarde` | mediana y máximo por ciudad |
| D22 flujo encuesta + `guarde` | `;`, renombre, conversión, orden |
| D23 columna reservada | `fecha` como columna (D5) |
| D24 anidados + `pare` | rompe solo el interno |
| D25 `devuelva` en ciclo | retorno temprano |
| D26 `repita 0 veces` | cuerpo no corre |

## Funciones (`funciones/`, 75 ejercicios)

| Carpeta | Contenido |
|---|---|
| `funciones/faciles/F01–F25` | funciones de 0–2 parámetros, aritmética y lógica |
| `funciones/medianos/M01–M25` | condicionales, composición, closures, uso en pipeline |
| `funciones/dificiles/D01–D25` | recursión (factorial, Fibonacci, MCD, Collatz), cadenas de llamadas |

Reglas semánticas aplicadas: `docs/09_reglas_semanticas.md`.
