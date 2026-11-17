# Pruebas y ejemplos verificables de AREPA

Esta carpeta contiene 24 ejemplos correctos y 29 programas que deben ser
rechazados. Cada ejemplo tiene resultados esperados independientes en
`esperados.json`: cambiar un cálculo, una fila o una predicción puede hacer
fallar la prueba aunque el programa termine sin errores.

La última verificación y las correcciones encontradas están en
[`REPORTE.md`](REPORTE.md).

Desde la raíz del proyecto, con Python 3.11 o posterior y las dependencias
de `requirements.txt` instaladas:

```bash
python ejercicios/pruebas/ejecutar.py
```

Para incluir también los 349 ejercicios de los cortes y la sección completa, los nueve ejemplos,
el caso de estudio y las diez suites internas; también comprueba los resultados
esperados de los 185 ejercicios añadidos:

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

El corredor funciona en Windows y Linux, devuelve código 1 ante cualquier
fallo y muestra el archivo y el campo que no coincide. Cada prueba nueva usa
una carpeta temporal con datos limpios; las gráficas no abren ventanas y las
salidas temporales se eliminan al terminar. Las suites internas conservan su
comportamiento habitual de escribir en `salidas/` del proyecto.

## Diagnósticos y avisos de consola

El [reporte de diagnósticos](REPORTE_DIAGNOSTICOS.md) registra la verificación.

Además de los 55 casos base, se incluyen automáticamente las **28 pruebas**
de `test_diagnosticos.py` (junto con 23 de auditoría y cuatro de entrega: 110 en el modo predeterminado). Comprueban
los 29 programas negativos por la CLI, el operador y la etapa que fallan,
datos de la fila, línea del CSV, llamadas a funciones, fuente no UTF-8,
fallos al guardar archivos, errores de argumentos y consola interactiva.

La división por cero, el módulo por cero y otras operaciones especiales
permitidas generan avisos con explicación; no se convierten en errores.
Se prueba que el programa continúa, que los avisos repetidos se agrupan y
que no se mezclan resultados positivos y negativos. Los cálculos ordinarios,
faltantes normales, tablas vacías permitidas y ramas sin ejecutar no deben
producir falsas alarmas.

```bash
python ejercicios/pruebas/test_diagnosticos.py
```

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

Los CSV se leen también con `csv.reader` de la biblioteca estándar de Python
para contrastar el escritor propio. Los PNG se verifican mediante firma,
dimensiones RGB de 800×480, bloques, CRC con `zlib`, descompresión completa,
longitud de las filas y variedad de colores. Se repite cada programa gráfico
para comprobar que produce los mismos bytes. Esto verifica integridad y
reproducibilidad; las pruebas internas del motor comprueban además cálculos,
escalas, cuartiles y contenido de las gráficas.

El corredor agrega comprobaciones de CSV multilínea con LF/CRLF, líneas vacías
dentro de campos, separadores diferentes, comillas literales y ubicación de
errores. También ejecuta la CLI real para verificar ejecución, árbol y
diagnósticos sin traceback de Python.

Para ver un ejemplo por consola y conservar sus archivos en `salidas/`:

```bash
python src/cli/main.py ejercicios/pruebas/positivos/01_potencias.arepa --ejecutar
python src/cli/main.py ejercicios/pruebas/positivos/11_flujo_completo.arepa --ejecutar --sin-ventana
```

## Ejemplos de errores

`negativos/` cubre variables, columnas y modelos inexistentes; tipos
incompatibles; potencias complejas; condiciones inválidas; índices 0 y fuera
de rango; filas incompletas; `pare/siga/devuelva` fuera de contexto; archivos
ausentes; guardar un número; fechas imposibles; gráficas vacías o con texto;
extensiones incorrectas; argumentos faltantes; paso cero; errores léxicos y
sintácticos; histogramas con varias series; cláusulas repetidas; CSV con exceso
de campos, comillas sin cerrar o totalmente vacío.

No basta con que fallen: se exige la clase de error AREPA y un fragmento de
diagnóstico esperado. Los programas con error de ejecución deben primero
superar el parser y no producir archivos.

## Relación con lo evaluado

Basado en las secciones 2, 5 y 6 de `docs/Proyecto_LP.pdf` y las matrices de
trazabilidad de los tres cortes.

| Criterio del enunciado | Peso sugerido | Evidencia reproducible |
|---|---:|---|
| Diseño y coherencia de sintaxis | 20 % | Ejemplos positivos, negativos, precedencia, funciones y pipelines; suites de front-end y árbol |
| Correctitud léxica, sintáctica y semántica | 25 % | Resultados esperados, 29 negativos, diagnósticos y suites internas |
| Implementación y calidad | 20 % | Pruebas de estructuras y Visitor mediante el ejecutor real; suites internas. La calidad y modularidad requieren también revisión del código |
| Funcionalidad del dominio | 20 % | Preparación, estadísticas, CSV, cinco gráficas, flujo completo y caso de estudio |
| Documentación, reproducibilidad y Git | 10 % | Comandos, datos incluidos, resultados esperados y reporte. El historial de Git se revisa aparte |
| Sustentación | 5 % | Ejemplos ejecutables para explicar resultados. La presentación se evalúa presencialmente |

Las pruebas respaldan el funcionamiento observado; no sustituyen la revisión
de documentos ni garantizan la ausencia de todos los errores posibles.

La ampliación y sus 25 preguntas de sustentación se describen en el
[catálogo de ejercicios](../CATALOGO.md). Se puede verificar por separado con
`python ejercicios/pruebas/ejecutar.py --ejercicios`.

## Auditoría adversarial y paquete de entrega

El corredor incorpora también `test_auditoria.py` (23 pruebas) y
`test_entrega.py` (cuatro pruebas). Cubren divergencia, NaN, infinitos,
columnas duplicadas, CSV sin pérdida de textos ni filas, enteros de más de
4.300 dígitos y un paquete reproducible con integridad SHA-256. Se verifican
casos extremos válidos para evitar falsos rechazos.

```bash
python ejercicios/pruebas/test_auditoria.py
python ejercicios/pruebas/test_entrega.py
python herramientas/verificar_entrega.py
python herramientas/crear_entrega.py --probar
```

El modo completo incorpora 469 pruebas del corredor y las 370 pruebas
internas; el modo `--ejercicios` ejecuta 295 pruebas. Los conteos de las diez
suites internas se mantienen separados de las pruebas nuevas de ejercicios.
