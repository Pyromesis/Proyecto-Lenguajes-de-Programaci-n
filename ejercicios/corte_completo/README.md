# Ejercicios del Corte completo

Todos los programas tienen solución completa y se ejecutan desde la raíz del proyecto.
Índice general: [ejercicios](../README.md).

| Carpeta | Programas |
|---|---:|
| `integradores/` | 12 |
| `sustentacion/` | 25 |

## Ejecutar y verificar

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

Los ejercicios nuevos se contrastan con resultados independientes en
`../resultados_esperados.json`: valores, filas, exportaciones CSV e integridad de PNG.
Cada archivo incluye su enunciado, los resultados esperados y el comando para ejecutarlo.

## Ruta de práctica

1. Resolver los integradores de ventas, encuestas, inventario y notas.
2. Entrenar y evaluar regresión, perceptrón y árbol con datos separados.
3. Ejecutar el caso público de pasajeros con cinco visualizaciones.
4. Preparar las 25 preguntas con su respuesta razonada y programa de demostración.

Las preguntas son propuestas de práctica; no son preguntas oficiales del docente.
Los datos sintéticos enseñan comportamiento conocido; I01, I02 e I12 usan CSV del proyecto.

## Ejercicios resueltos

### Integradores

| Ejercicio | Enunciado |
|---|---|
| [I01_ventas_reales](integradores/I01_ventas_reales.arepa) | Cargar el CSV de ventas, calcular ingreso por ciudad, exportar y graficar. |
| [I02_encuesta_limpieza](integradores/I02_encuesta_limpieza.arepa) | Cargar encuesta con separador punto y coma, descartar ingresos vacíos y obtener el conteo por ciudad. |
| [I03_inventario](integradores/I03_inventario.arepa) | Actualizar existencias con movimientos, marcar necesidades y exportar las cantidades finales. |
| [I04_notas_academicas](integradores/I04_notas_academicas.arepa) | Limpiar notas, clasificar aprobados y calcular estadísticas por curso. |
| [I05_regresion_vivienda](integradores/I05_regresion_vivienda.arepa) | Entrenar con cinco viviendas y evaluar tres áreas nuevas sin usarlas en el ajuste. |
| [I06_clasificacion_estudiantes](integradores/I06_clasificacion_estudiantes.arepa) | Aprender dos clases y exportar predicciones de estudiantes nuevos con métricas. |
| [I07_arbol_riesgo](integradores/I07_arbol_riesgo.arepa) | Aprender tres niveles de riesgo con un árbol y resumir las clases de datos nuevos. |
| [I08_simulacion_ahorro](integradores/I08_simulacion_ahorro.arepa) | Simular un saldo inicial de cien con depósitos de veinte en cuatro meses. |
| [I09_control_calidad](integradores/I09_control_calidad.arepa) | Clasificar mediciones dentro de tolerancia y calcular el porcentaje aceptado por lote. |
| [I10_ventas_funciones](integradores/I10_ventas_funciones.arepa) | Aplicar descuento por volumen a cada línea y resumir el ingreso por producto. |
| [I11_estadisticas_robustas](integradores/I11_estadisticas_robustas.arepa) | Contrastar media, mediana y rango de dos muestras, una con dato extremo. |
| [I12_pasajeros_publicos](integradores/I12_pasajeros_publicos.arepa) | Analizar las 144 observaciones públicas y exportar un resumen anual más cinco gráficas. |

### Preguntas de sustentación resueltas

#### [S01_precedencia](sustentacion/S01_precedencia.arepa) — ¿Por qué 2 + 3 * 4 da 14 y (2 + 3) * 4 da 20?

El producto tiene mayor prioridad que la suma; los paréntesis cambian el árbol de análisis.

#### [S02_potencia_unario](sustentacion/S02_potencia_unario.arepa) — ¿Cuánto dan -2 ^ 2, (-2) ^ 2 y 2 ^ 3 ^ 2?

La potencia precede al menos unario y se asocia hacia la derecha.

#### [S03_lexico_unicode](sustentacion/S03_lexico_unicode.arepa) — ¿Se admiten identificadores con ñ y tildes y cómo se ve su token?

Los identificadores admiten Unicode; ejecutar también con --tokens para observar ID y literales.

#### [S04_sintaxis_bloques](sustentacion/S04_sintaxis_bloques.arepa) — ¿Cómo separa AREPA las sentencias y delimita un bloque?

Los saltos separan sentencias; quihubo y chao delimitan el programa y las llaves delimitan bloques.

#### [S05_nada_logica](sustentacion/S05_nada_logica.arepa) — ¿Por qué nada == nada produce nada y el filtro descarta esa fila?

Las comparaciones propagan nada; el filtro conserva únicamente resultados obvio.

#### [S06_division_cero](sustentacion/S06_division_cero.arepa) — ¿Se detiene el programa al dividir entre cero?

1/0 y -1/0 son infinitos; 0/0 y el módulo por cero producen nada.

#### [S07_declaracion_variable](sustentacion/S07_declaracion_variable.arepa) — ¿Cómo se evita una variable no declarada?

Se asigna antes de consultar; negativos/01_variable.arepa demuestra el rechazo de una referencia ausente.

#### [S08_columna_vs_variable](sustentacion/S08_columna_vs_variable.arepa) — Si hay una columna x y una variable x, ¿cuál usa un pipeline?

En una expresión por fila se busca primero la columna; fuera del pipeline se usa la variable.

#### [S09_pipeline_no_muta](sustentacion/S09_pipeline_no_muta.arepa) — ¿Un pipeline cambia la tabla original?

Cada etapa produce una tabla nueva; las asignaciones indexadas sí son mutación explícita.

#### [S10_closure_referencia](sustentacion/S10_closure_referencia.arepa) — ¿Una función captura una copia del valor global o el entorno?

Captura el entorno por referencia y ve las reasignaciones posteriores de una variable existente.

#### [S11_parametros_ambito](sustentacion/S11_parametros_ambito.arepa) — ¿Un parámetro con el mismo nombre cambia la variable global?

El parámetro vive en el ámbito local de la llamada y oculta la variable global homónima.

#### [S12_recursion_base](sustentacion/S12_recursion_base.arepa) — ¿Comprobación que factorial termina y qué devuelve para cero?

El caso base n menor o igual que uno devuelve uno; cada llamada reduce n.

#### [S13_pare_devuelva](sustentacion/S13_pare_devuelva.arepa) — ¿Qué diferencia hay entre pare y devuelva dentro de un ciclo?

pare termina el ciclo actual; devuelva termina la función y entrega un valor.

#### [S14_siga_acumulacion](sustentacion/S14_siga_acumulacion.arepa) — ¿Cómo se suman solo impares usando siga?

siga omite el resto de la vuelta actual; no termina el ciclo.

#### [S15_snapshot_recorrido](sustentacion/S15_snapshot_recorrido.arepa) — ¿Agregar elementos durante recorra provoca un ciclo infinito?

El recorrido usa una instantánea de los elementos iniciales; las inserciones no añaden vueltas.

#### [S16_indices_desde_uno](sustentacion/S16_indices_desde_uno.arepa) — ¿Cuál es el primer índice y cómo se accede a una celda?

El primer índice es uno; una celda se consulta con fila y nombre de columna.

#### [S17_mutacion_fila](sustentacion/S17_mutacion_fila.arepa) — ¿Cómo se sustituye una fila sin perder la correspondencia entre columnas?

Una lista respeta el orden de columnas; un registro se asigna por nombres de clave.

#### [S18_csv_comillas](sustentacion/S18_csv_comillas.arepa) — ¿Cómo se conserva una coma y una comilla dentro de un campo CSV?

El escritor entrecomilla el campo y duplica comillas internas; el lector reconstruye el texto.

#### [S19_cuente_y_nada](sustentacion/S19_cuente_y_nada.arepa) — ¿Por qué cuente() y cuente(columna) pueden dar resultados diferentes?

El primero cuenta filas y el segundo valores presentes; las demás agregaciones ignoran nada.

#### [S20_desviacion_poblacional](sustentacion/S20_desviacion_poblacional.arepa) — ¿La desviación divide entre n o entre n menos uno?

AREPA calcula la desviación poblacional: divide entre n; para 1 y 3 devuelve uno.

#### [S21_promedios_ponderados](sustentacion/S21_promedios_ponderados.arepa) — ¿Se puede promediar la media de grupos de distinto tamaño?

Solo con ponderación por cantidad se obtiene la media global; el promedio simple puede sesgar el resultado.

#### [S22_barras_agrupacion](sustentacion/S22_barras_agrupacion.arepa) — ¿Cómo se hace explícita la suma de observaciones con igual categoría?

Agrupar y resumir produce una fila por categoría y hace verificable la altura esperada de cada barra.

#### [S23_cajas_y_atipicos](sustentacion/S23_cajas_y_atipicos.arepa) — ¿Por qué usar cajas para comparar grupos con valores extremos?

Permiten comparar medianas y dispersión; la media cambia mucho con un extremo y la mediana puede mantenerse.

#### [S24_png_reproducible](sustentacion/S24_png_reproducible.arepa) — ¿Cómo se demuestra que pinte genera un PNG válido y reproducible?

Exportar con guardela y ejecutar las pruebas que verifican CRC, descompresión, tamaño y repetición byte a byte.

#### [S25_separar_entrenamiento](sustentacion/S25_separar_entrenamiento.arepa) — ¿Por qué evaluar con observaciones separadas de entrenamiento?

Evaluar sobre entradas nuevas evita confundir memorización con generalización; este ejemplo mantiene ambos conjuntos separados.

Para demostrar errores léxicos, sintácticos y semánticos, contrastar estas
soluciones con los [29 ejemplos negativos](../pruebas/README.md).
