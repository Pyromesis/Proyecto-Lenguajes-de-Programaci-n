# Ejercicios del Corte 3

Todos los programas tienen solución completa y se ejecutan desde la raíz del proyecto.
Índice general: [ejercicios](../README.md).

| Carpeta | Programas |
|---|---:|
| `faciles/` | 25 |
| `medianos/` | 25 |
| `dificiles/` | 25 |
| `graficas/` | 12 |

## Ejecutar y verificar

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

Los ejercicios nuevos se contrastan con resultados independientes en
`../resultados_esperados.json`: valores, filas, exportaciones CSV e integridad de PNG.
Cada archivo incluye su enunciado, los resultados esperados y el comando para ejecutarlo.

## Ejercicios añadidos con resultados comprobables

### faciles

| Ejercicio | Enunciado |
|---|---|
| [F01_ventas_dia](faciles/F01_ventas_dia.arepa) | Comparar las ventas de lunes, martes y miércoles. |
| [F02_gastos_categoria](faciles/F02_gastos_categoria.arepa) | Comparar gastos de alimentación, transporte y vivienda. |
| [F03_alumnos_curso](faciles/F03_alumnos_curso.arepa) | Comparar la matrícula de tres cursos. |
| [F04_stock_producto](faciles/F04_stock_producto.arepa) | Mostrar las existencias de arroz, leche y café. |
| [F05_votos_opcion](faciles/F05_votos_opcion.arepa) | Comparar el número de votos de tres opciones. |
| [F06_temperatura_dia](faciles/F06_temperatura_dia.arepa) | Representar la evolución de temperatura durante cuatro días. |
| [F07_ahorro_mes](faciles/F07_ahorro_mes.arepa) | Representar el saldo acumulado durante cuatro meses. |
| [F08_visitas_semana](faciles/F08_visitas_semana.arepa) | Representar las visitas de una web durante cuatro semanas. |
| [F09_poblacion_anio](faciles/F09_poblacion_anio.arepa) | Mostrar el crecimiento de una población durante cuatro años. |
| [F10_distancia_tiempo](faciles/F10_distancia_tiempo.arepa) | Representar la distancia recorrida por un móvil a velocidad constante. |
| [F11_notas](faciles/F11_notas.arepa) | Observar cómo se distribuyen diez calificaciones. |
| [F12_edades](faciles/F12_edades.arepa) | Observar la distribución de edades de ocho personas. |
| [F13_tiempos](faciles/F13_tiempos.arepa) | Representar la distribución de ocho tiempos de atención. |
| [F14_importes](faciles/F14_importes.arepa) | Representar la distribución de importes de ocho compras. |
| [F15_estaturas](faciles/F15_estaturas.arepa) | Representar la distribución de ocho estaturas en centímetros. |
| [F16_publicidad_ventas](faciles/F16_publicidad_ventas.arepa) | Explorar la relación entre inversión publicitaria y ventas. |
| [F17_estudio_nota](faciles/F17_estudio_nota.arepa) | Explorar la relación entre horas de estudio y nota obtenida. |
| [F18_area_precio](faciles/F18_area_precio.arepa) | Comparar áreas y precios de cuatro viviendas. |
| [F19_horas_consumo](faciles/F19_horas_consumo.arepa) | Relacionar horas de uso con consumo eléctrico. |
| [F20_altura_peso](faciles/F20_altura_peso.arepa) | Explorar la relación entre altura y peso en cuatro observaciones. |
| [F21_salarios_area](faciles/F21_salarios_area.arepa) | Comparar dispersión salarial entre dos áreas. |
| [F22_notas_curso](faciles/F22_notas_curso.arepa) | Comparar medianas y variación de notas en dos cursos. |
| [F23_tiempo_servicio](faciles/F23_tiempo_servicio.arepa) | Comparar tiempos de dos servicios con tres observaciones cada uno. |
| [F24_precio_tienda](faciles/F24_precio_tienda.arepa) | Comparar la distribución de precios de dos tiendas. |
| [F25_lluvia_estacion](faciles/F25_lluvia_estacion.arepa) | Comparar mediciones de lluvia en dos estaciones. |

### medianos

| Ejercicio | Enunciado |
|---|---|
| [M01_ventas_agrupadas](medianos/M01_ventas_agrupadas.arepa) | Agrupar ventas repetidas por ciudad y mostrar el ingreso total. |
| [M02_stock_filtrado](medianos/M02_stock_filtrado.arepa) | Eliminar productos sin stock antes de graficar. |
| [M03_total_calculado](medianos/M03_total_calculado.arepa) | Calcular unidades por precio y mostrar el importe de cada producto. |
| [M04_categorias_ordenadas](medianos/M04_categorias_ordenadas.arepa) | Ordenar categorías por importe descendente antes de graficar. |
| [M05_duplicados](medianos/M05_duplicados.arepa) | Eliminar filas duplicadas antes de contar personas por ciudad. |
| [M06_dos_series](medianos/M06_dos_series.arepa) | Representar ingresos y egresos durante tres meses. |
| [M07_orden_temporal](medianos/M07_orden_temporal.arepa) | Ordenar días desordenados antes de unir los puntos. |
| [M08_saldo_neto](medianos/M08_saldo_neto.arepa) | Crear una serie de ingreso menos gasto por mes. |
| [M09_fechas_convertidas](medianos/M09_fechas_convertidas.arepa) | Convertir fechas válidas y representar su serie. |
| [M10_relleno_vacios](medianos/M10_relleno_vacios.arepa) | Reemplazar una observación faltante por cero antes de graficar. |
| [M11_notas_validas](medianos/M11_notas_validas.arepa) | Descartar notas fuera del intervalo entre cero y cinco. |
| [M12_texto_numero](medianos/M12_texto_numero.arepa) | Convertir edades almacenadas como texto antes de graficar. |
| [M13_cuadrados](medianos/M13_cuadrados.arepa) | Crear una columna cuadrado y mostrar su distribución. |
| [M14_sin_faltantes](medianos/M14_sin_faltantes.arepa) | Eliminar valores nada antes de representar tiempos. |
| [M15_importes_descontados](medianos/M15_importes_descontados.arepa) | Aplicar diez por ciento de descuento antes del histograma. |
| [M16_precio_importe](medianos/M16_precio_importe.arepa) | Calcular importe y relacionarlo con precio. |
| [M17_solo_aprobados](medianos/M17_solo_aprobados.arepa) | Filtrar estudiantes aprobados antes de relacionar horas y nota. |
| [M18_renombre_ejes](medianos/M18_renombre_ejes.arepa) | Cambiar x e y por nombres de dominio y utilizarlos como ejes. |
| [M19_seleccionar_ejes](medianos/M19_seleccionar_ejes.arepa) | Quitar una columna auxiliar antes de representar área y precio. |
| [M20_funcion_cuadratica](medianos/M20_funcion_cuadratica.arepa) | Usar una función para calcular los puntos de una parábola. |
| [M21_salarios_limpios](medianos/M21_salarios_limpios.arepa) | Excluir salarios negativos y conservar las dos áreas. |
| [M22_conversion_notas](medianos/M22_conversion_notas.arepa) | Convertir notas textuales para comparar dos cursos. |
| [M23_sin_duplicados](medianos/M23_sin_duplicados.arepa) | Eliminar duplicados exactos antes de comparar distribuciones. |
| [M24_grupo_numerico](medianos/M24_grupo_numerico.arepa) | Comparar observaciones de dos grupos identificados por números. |
| [M25_sin_eje_x](medianos/M25_sin_eje_x.arepa) | Comparar dos columnas numéricas sin columna de agrupación x. |

### dificiles

| Ejercicio | Enunciado |
|---|---|
| [D01_balance_financiero](dificiles/D01_balance_financiero.arepa) | Calcular ingresos y gastos por mes y representar ambas series y su balance. |
| [D02_regresion_predicciones](dificiles/D02_regresion_predicciones.arepa) | Aprender una recta y comparar valores reales y predichos sobre datos nuevos. |
| [D03_perceptron_conteos](dificiles/D03_perceptron_conteos.arepa) | Entrenar un perceptrón y representar el conteo de predicciones sobre datos separados. |
| [D04_arbol_multiclase](dificiles/D04_arbol_multiclase.arepa) | Clasificar tres rangos y resumir las predicciones de observaciones nuevas. |
| [D05_acumulados](dificiles/D05_acumulados.arepa) | Construir ventas acumuladas mediante recorrido y comparar con las ventas diarias. |
| [D06_media_movil](dificiles/D06_media_movil.arepa) | Suavizar una serie con ventanas completas de tres observaciones. |
| [D07_estandarizacion](dificiles/D07_estandarizacion.arepa) | Calcular puntuaciones z y verificar media cero y desviación uno. |
| [D08_escala_minmax](dificiles/D08_escala_minmax.arepa) | Normalizar con mínimo y máximo y comprobar los extremos de la escala. |
| [D09_tasas_por_grupo](dificiles/D09_tasas_por_grupo.arepa) | Calcular porcentaje de aprobados por curso mediante una función indicadora. |
| [D10_crecimiento_relativo](dificiles/D10_crecimiento_relativo.arepa) | Calcular la variación porcentual entre periodos sucesivos. |
| [D11_interes_compuesto](dificiles/D11_interes_compuesto.arepa) | Simular tres años al diez por ciento y contrastar con una fórmula de potencia. |
| [D12_amortizacion](dificiles/D12_amortizacion.arepa) | Simular pagos de 40 con interés de diez por ciento hasta cancelar la deuda. |
| [D13_tarifa_por_tramos](dificiles/D13_tarifa_por_tramos.arepa) | Calcular facturas con primeros diez consumos a dos y el resto a tres. |
| [D14_factorial_vs_cuadrado](dificiles/D14_factorial_vs_cuadrado.arepa) | Generar factorial y cuadrado para los enteros de uno a cinco. |
| [D15_fibonacci_razones](dificiles/D15_fibonacci_razones.arepa) | Construir términos consecutivos y representar sus cocientes. |
| [D16_atipicos_mediana](dificiles/D16_atipicos_mediana.arepa) | Comparar el efecto de un valor extremo en dos grupos antes de dibujar cajas. |
| [D17_residuos_modelo](dificiles/D17_residuos_modelo.arepa) | Calcular residuos de una recta propuesta y su error cuadrático medio. |
| [D18_participacion_porcentual](dificiles/D18_participacion_porcentual.arepa) | Agrupar categorías y calcular qué porcentaje del total representa cada una. |
| [D19_tres_series_transformadas](dificiles/D19_tres_series_transformadas.arepa) | Comparar funciones lineal, cuadrática y cúbica para entradas con negativos. |
| [D20_exportar_releer](dificiles/D20_exportar_releer.arepa) | Exportar un resumen y generar una gráfica desde el CSV releído. |
| [D21_resumen_doble](dificiles/D21_resumen_doble.arepa) | Obtener subtotales por región y producto antes de resumir por región. |
| [D22_seleccion_closure](dificiles/D22_seleccion_closure.arepa) | Definir un filtro por umbral, cambiarlo y comprobar las dos selecciones. |
| [D23_intervalos_estadisticos](dificiles/D23_intervalos_estadisticos.arepa) | Mostrar media, mediana y desviación calculadas sobre cada grupo. |
| [D24_tiempo_continuo](dificiles/D24_tiempo_continuo.arepa) | Convertir año y mes a un eje continuo y agrupar meses repetidos. |
| [D25_cinco_vistas](dificiles/D25_cinco_vistas.arepa) | Crear un resumen y las cinco visualizaciones del mismo conjunto de datos. |
