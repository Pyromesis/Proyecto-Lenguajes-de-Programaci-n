# Ejercicios y problemas AREPA

**164 programas** `.arepa` de práctica, organizados por corte. Todos validan
(`python3 src/cli/main.py <archivo>`) y ejecutan
(`--ejecutar`) desde la raíz del proyecto. Las rutas `datos/...` y
`caso_estudio/...` se resuelven desde ahí.

```bash
# Un ejercicio del Corte 1
python3 src/cli/main.py ejercicios/corte1/faciles/F01_programa_minimo.arepa --ejecutar

# Un ejercicio del Corte 3 (sin abrir ventana)
python3 src/cli/main.py ejercicios/corte3/graficas/G01_barras_ciudad.arepa --ejecutar --sin-ventana
```

## Estructura

```text
ejercicios/
├── README.md                 este índice
├── datos/                    CSV compartidos por los ejercicios
├── corte1/                   32 ejercicios: front-end, expresiones y pipeline
│   ├── faciles/              F01-F11
│   ├── medianos/             M01-M10
│   └── dificiles/            D01-D11
├── corte2/                   120 ejercicios: semántica, datos y funciones
│   ├── faciles/              F12-F26
│   ├── medianos/             M11-M25
│   ├── dificiles/            D12-D26
│   └── funciones/            75 ejercicios (F01-F25, M01-M25, D01-D25)
└── corte3/                   12 ejercicios: visualización y PNG
    └── graficas/             G01-G12
```

Convenciones de nombre: `F` fácil, `M` mediano, `D` difícil y `G` gráficas.
Cada archivo indica en sus primeras líneas el concepto que ejercita. Los que
usan `guarde` o `guardela` escriben en `salidas/` (temporal, ignorado por git).

## Corte 1 — front-end y fundamentos (32)

| Carpeta | Contenido |
|---|---|
| `corte1/faciles/F01-F11` | programa mínimo, asignaciones, literales, comentarios, operadores, lógicos, `cuenteme`/`describa`, `monte`, `escoja`, condicional, división |
| `corte1/medianos/M01-M10` | precedencia, pipeline+filtro, `acomode`, `limpie`, `cree`+`renombre`, `convierta`, `invente`, `sino`, `resuma`, `pinte` |
| `corte1/dificiles/D01-D11` | potencia/unarios, Unicode, `nada`, closures, estadísticas, merge sort, bisiestos, CSV con comillas, `guarde`, flujo completo, bordes |

## Corte 2 — semántica, datos y funciones (120)

| Carpeta | Contenido |
|---|---|
| `corte2/faciles/F12-F26` | filtro, columna calculada, orden, renombre, conversión, duplicados, vacíos, `guarde`, agregaciones, `describa`, ciclos |
| `corte2/medianos/M11-M25` | pipelines, filtros compuestos, doble clave, fechas, juntes, agregaciones, rangos, `pare`, `sino`, closures, `pinte` |
| `corte2/dificiles/D12-D26` | `resuma` sin junte, `nada`, tabla vacía, medianas, desviación, `pare`/`siga`, factorial, flujos con `guarde`, anidados, retorno temprano |
| `corte2/funciones/faciles` | funciones de 0–2 parámetros, aritmética y lógica |
| `corte2/funciones/medianos` | condicionales, composición, closures y uso en pipeline |
| `corte2/funciones/dificiles` | recursión (factorial, Fibonacci, MCD, Collatz) y cadenas de llamadas |

## Corte 3 — visualización y producto final (12)

| Ejercicio | Qué ejercita |
|---|---|
| `G01_barras_ciudad` | barras con agrupación y suma |
| `G02_lineas_dos_series` | `ejey [col1, col2]` y leyenda |
| `G03_histograma_unidades` | histograma de una columna |
| `G04_dispersion_precio` | dispersión con `ejex`/`ejey` numéricos |
| `G05_cajas_ciudad` | cajas agrupadas por categoría repetida |
| `G06_estetica_completa` | título, ejes y leyenda en una gráfica |
| `G07_muestrela` | salida automática en `salidas/` y `--sin-ventana` |
| `G08_pipeline_grafica` | filtro, columna calculada, junte, `resuma` y PNG |
| `G09_serie_temporal` | eje x continuo a partir de año y mes |
| `G10_cajas_decadas` | cajas agrupadas por x numérica repetida |
| `G11_histograma_ingresos` | histograma de una columna calculada |
| `G12_cinco_graficas` | las cinco gráficas en un solo programa |

## Datos compartidos

`ejercicios/datos/` contiene los casos borde del lector CSV propio:

| Archivo | Uso |
|---|---|
| `vacia.csv` | tabla sin filas |
| `comillas.csv` | comillas, comas y saltos dentro de campos |

Los conjuntos generales están en `datos/` (`ventas.csv`, `empleados.csv`,
`encuesta.csv`) y el caso de estudio en `caso_estudio/datos/pasajeros.csv`.

## Regresión

```bash
bash herramientas/regresion_programas.sh
```

Ejecuta los 164 ejercicios y los 6 ejemplos (170 programas) con
`--ejecutar --sin-ventana` desde la raíz y falla si alguno no termina con
código 0. Reglas semánticas aplicadas: `docs/09_reglas_semanticas.md`.
