# Pruebas y ejemplos verificables

El corredor ejecuta programas completos y contrasta sus resultados con
`esperados.json` y `../resultados_esperados.json`. Los 24 ejemplos positivos
demuestran el comportamiento esperado; los 29 negativos comprueban el
rechazo y la causa del error.

## Ejecución

Desde la raíz del proyecto, con Python 3.11 o posterior y las dependencias
de `requirements.txt` instaladas:

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

| Modo | Cobertura | Pruebas del corredor | Pruebas internas |
|---|---|---:|---:|
| Sin opciones | 55 casos base, 28 de diagnósticos, 23 de auditoría y 4 de entrega | 110 | — |
| `--ejercicios` | Modo base y resultados esperados de los 185 ejercicios añadidos | 295 | — |
| `--completo` | Lo anterior, los programas restantes, nueve ejemplos, caso de estudio y suites internas | 469 | 370 en 10 suites |

El corredor devuelve código 1 si falla una comprobación e identifica el
archivo y el resultado que no coincide. Cada caso nuevo utiliza datos y
salidas temporales; las gráficas se generan sin abrir ventanas. Las suites
internas pueden escribir en `salidas/`.

## Qué se comprueba

| Área | Comprobación |
|---|---|
| Valores y tablas | Resultados independientes, filas, columnas y tolerancia numérica de `1e-7` |
| CSV | Relectura con `csv.reader`, separadores, comillas, saltos de línea, espacios, tipos y faltantes |
| PNG | Firma, dimensiones RGB de 800 × 480, bloques, CRC, descompresión y contenido no uniforme |
| Reproducibilidad gráfica | Dos ejecuciones producen los mismos bytes |
| Programas inválidos | Clase de error y fragmento de diagnóstico esperado; los errores de ejecución superan primero el parser |
| Consola | Validación, ejecución, árbol, argumentos, ubicación, ayuda y ausencia de traceback |
| Límites numéricos | Divergencia, valores no finitos, enteros extensos y casos extremos válidos |
| Entrega | ZIP determinista, manifiesto SHA-256, detección de alteraciones y rutas de extracción |

Las pruebas internas del motor gráfico contrastan también escalas, cuartiles
y cálculos de dibujo. La integridad del PNG se comprueba por separado de esos
resultados estadísticos.

## Ejemplos correctos

| Programa en `positivos/` | Qué demuestra y comprueba |
|---|---|
| `01_potencias.arepa` | `2 ^ 3 ^ 2 = 512`, `-2 ^ 2 = -4`, `(-2) ^ 2 = 4`, exponentes negativos, raíces, módulo y precedencia |
| `02_logica_y_nada.arepa` | Los seis operadores relacionales, `y/o/no`, propagación de `nada`, división y módulo por cero |
| `03_funciones_y_recursion.arepa` | Elevar con parámetros, factorial de 0 y 6, retorno, condicionales y captura de una variable reasignada |
| `04_ciclos.arepa` | Rangos ascendentes/descendentes, paso negativo, `mientras`, cero repeticiones, `pare` y `siga` |
| `05_estructuras.arepa` | Listas, registros, tablas, índices desde 1, mutación, inserción, eliminación, recorrido y nombres de columnas |
| `06_pipeline_no_muta.arepa` | Selección, filtro compuesto, columna calculada, renombre y orden; compara también que el original se conserva |
| `07_limpieza_y_conversion.arepa` | Duplicados, relleno y eliminación de vacíos, número/texto y fecha bisiesta válida |
| `08_estadisticas.arepa` | Conteo total y de valores, suma, media, mediana par/impar, mínimo, máximo y desviación poblacional; ignora faltantes |
| `09_orden_y_dos_claves.arepa` | Orden estable con empates y faltantes, agrupación por dos columnas |
| `10_csv_ida_y_vuelta.arepa` | Comas, comillas escapadas, tildes y saltos de línea dentro de campos; exportación y relectura sin pérdida |
| `11_flujo_completo.arepa` | Carga con `;`, filtro, cálculo, agrupación, resumen, descripción, CSV y gráfica; ingresos esperados: Bogotá 25, Cali 12 |
| `12_grafica_barras.arepa` | Barras con categorías repetidas |
| `13_grafica_lineas.arepa` | Líneas con dos series en `ejey` |
| `14_grafica_histograma.arepa` | Distribución de una columna |
| `15_grafica_dispersion.arepa` | Dispersión con dos ejes numéricos |
| `16_grafica_cajas.arepa` | Cajas con valores repetidos en x |
| `17_muestrela.arepa` | Nombre de salida automático y ejecución sin ventana |
| `18_regresion.arepa` | Aprende `respuesta = 2*x + 3`; predice 17 y 19 sobre entradas nuevas y muestra métricas |
| `19_perceptron.arepa` | Clasificación binaria sobre entradas nuevas y matriz de confusión |
| `20_arbol.arepa` | Árbol de decisión sobre entradas nuevas y métricas |
| `21_csv_sin_encabezado.arepa` | Separador configurable y nombres automáticos de columnas |
| `22_filtro_nada_y_vacio.arepa` | Descarta faltantes al filtrar y comprueba estadísticas sobre una tabla vacía |
| `23_orden_descendente_estable.arepa` | Empates estables en descenso y faltantes al final |
| `24_unicode_y_literales.arepa` | Identificadores con ñ/tildes, decimales, cadenas escapadas y claves con espacios |

Para ejecutar un ejemplo y conservar sus archivos:

```bash
python src/cli/main.py ejercicios/pruebas/positivos/01_potencias.arepa --ejecutar
python src/cli/main.py ejercicios/pruebas/positivos/11_flujo_completo.arepa --ejecutar --sin-ventana
```

## Diagnósticos y casos negativos

Los programas de `negativos/` cubren nombres inexistentes, tipos
incompatibles, índices inválidos, filas incompletas, control de flujo fuera
de contexto, fechas imposibles, archivos ausentes, gráficas inválidas y
errores léxicos, sintácticos o de formato CSV.

`test_diagnosticos.py` contrasta la ubicación y la causa del error, el
contexto de filas y llamadas, la lectura de fuentes y los fallos al guardar.
En la consola interactiva, un fallo al guardar conserva el contenido y la sesión.
También comprueba los avisos aritméticos y su agrupación. Dividir entre cero
puede producir un valor especial y permitir la continuación según las
reglas del lenguaje. Los cálculos ordinarios, los faltantes normales y las
ramas sin ejecutar no deben generar falsas alarmas.

## Comprobaciones específicas

```bash
python ejercicios/pruebas/test_diagnosticos.py
python ejercicios/pruebas/test_auditoria.py
python ejercicios/pruebas/test_entrega.py
```

El [índice de pruebas internas](../../pruebas/README.md) describe las diez
suites. El [catálogo](../CATALOGO.md) organiza los ejercicios por área y el
[informe de verificación técnica](../../docs/13_cierre_tecnico.md) conserva
los resultados y las correcciones comprobadas.
