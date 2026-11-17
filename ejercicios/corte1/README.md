# Ejercicios del Corte 1

Todos los programas tienen solución completa y se ejecutan desde la raíz del proyecto.
Índice general: [ejercicios](../README.md).

| Carpeta | Programas |
|---|---:|
| `faciles/` | 25 |
| `medianos/` | 25 |
| `dificiles/` | 25 |

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
| [F12_potencia_cuadrado](faciles/F12_potencia_cuadrado.arepa) | Elevar 7 al cuadrado y mostrar 49. |
| [F13_potencia_cubo](faciles/F13_potencia_cubo.arepa) | Calcular el volumen de un cubo de lado 4. |
| [F14_promedio_notas](faciles/F14_promedio_notas.arepa) | Promediar 3, 4 y 5 respetando los paréntesis. |
| [F15_conversion_temperatura](faciles/F15_conversion_temperatura.arepa) | Convertir 25 grados Celsius a Fahrenheit. |
| [F16_porcentaje_descuento](faciles/F16_porcentaje_descuento.arepa) | Aplicar 15 por ciento de descuento a 200. |
| [F17_modulo_reparto](faciles/F17_modulo_reparto.arepa) | Hallar cuántos elementos sobran al repartir 29 entre 6. |
| [F18_comparacion_edad](faciles/F18_comparacion_edad.arepa) | Determinar si una persona de 18 años es mayor de edad. |
| [F19_intervalo_cerrado](faciles/F19_intervalo_cerrado.arepa) | Comprobar que 5 pertenece al intervalo cerrado de 1 a 10. |
| [F20_identificador_unicode](faciles/F20_identificador_unicode.arepa) | Calcular los meses de dos años con una variable que contiene ñ. |
| [F21_texto_escapes](faciles/F21_texto_escapes.arepa) | Contar los caracteres de la palabra Bogotá. |
| [F22_exponente_negativo](faciles/F22_exponente_negativo.arepa) | Calcular el inverso de ocho usando una potencia. |
| [F23_raiz_por_potencia](faciles/F23_raiz_por_potencia.arepa) | Calcular la raíz cuadrada de 81. |
| [F24_parentesis_descuento](faciles/F24_parentesis_descuento.arepa) | Calcular el total de tres productos de 10 y un envío de 5. |
| [F25_reasignacion_saldo](faciles/F25_reasignacion_saldo.arepa) | Partir de 100, retirar 25 y depositar 40. |

### medianos

| Ejercicio | Enunciado |
|---|---|
| [M11_potencia_asociativa](medianos/M11_potencia_asociativa.arepa) | Comparar 2 elevado a 3 elevado a 2 con la variante entre paréntesis. |
| [M12_unario_potencia](medianos/M12_unario_potencia.arepa) | Comparar -3 al cuadrado con (-3) al cuadrado. |
| [M13_condicional_tarifa](medianos/M13_condicional_tarifa.arepa) | Cobrar 5 a un niño de 10 años y 10 al resto. |
| [M14_comparaciones_seis](medianos/M14_comparaciones_seis.arepa) | Evaluar las seis comparaciones numéricas con valores conocidos. |
| [M15_filtro_doble](medianos/M15_filtro_doble.arepa) | Conservar artículos con existencias positivas y precio menor que 20. |
| [M16_seleccion_orden_columnas](medianos/M16_seleccion_orden_columnas.arepa) | Reorganizar una tabla para mostrar precio antes de producto. |
| [M17_tabla_calculada](medianos/M17_tabla_calculada.arepa) | Multiplicar unidades por precio en dos filas. |
| [M18_renombrar_columna](medianos/M18_renombrar_columna.arepa) | Renombrar precio como valor sin perder filas. |
| [M19_nada_en_filtro](medianos/M19_nada_en_filtro.arepa) | Conservar solo los valores mayores que 1 y descartar nada. |
| [M20_logica_acceso](medianos/M20_logica_acceso.arepa) | Autorizar a un usuario activo que sea administrador o propietario. |
| [M21_funcion_area](medianos/M21_funcion_area.arepa) | Definir una función de área y usarla con dos rectángulos. |
| [M22_orden_texto](medianos/M22_orden_texto.arepa) | Ordenar tres ciudades alfabéticamente. |
| [M23_resumen_sencillo](medianos/M23_resumen_sencillo.arepa) | Contar y promediar tres notas. |
| [M24_conversion_numerica](medianos/M24_conversion_numerica.arepa) | Convertir textos 10 y 20 a números y sumarlos. |
| [M25_pipeline_inmutable](medianos/M25_pipeline_inmutable.arepa) | Crear una columna sin cambiar el número de columnas del origen. |

### dificiles

| Ejercicio | Enunciado |
|---|---|
| [D12_identidades_potencia](dificiles/D12_identidades_potencia.arepa) | Comprobar exponentes cero, uno, negativos y potencias encadenadas. |
| [D13_condicional_anidado](dificiles/D13_condicional_anidado.arepa) | Clasificar 4.5 como excelente usando decisiones anidadas. |
| [D14_comparacion_nada](dificiles/D14_comparacion_nada.arepa) | Mostrar que comparar nada no equivale a verdadero ni falso. |
| [D15_division_extremos](dificiles/D15_division_extremos.arepa) | Contrastar infinito positivo, negativo y cero dividido entre cero. |
| [D16_agrupacion_doble](dificiles/D16_agrupacion_doble.arepa) | Sumar ventas por ciudad y categoría. |
| [D17_orden_empates](dificiles/D17_orden_empates.arepa) | Ordenar por puntuación sin invertir las filas empatadas. |
| [D18_renombre_reservada](dificiles/D18_renombre_reservada.arepa) | Leer una columna llamada numero y renombrarla. |
| [D19_funcion_en_columna](dificiles/D19_funcion_en_columna.arepa) | Crear una columna con una función de impuesto. |
| [D20_filtro_demorgan](dificiles/D20_filtro_demorgan.arepa) | Comparar dos filtros equivalentes por De Morgan. |
| [D21_csv_multilinea](dificiles/D21_csv_multilinea.arepa) | Leer comillas y saltos de línea dentro de campos CSV. |
| [D22_estadisticas_sin_datos](dificiles/D22_estadisticas_sin_datos.arepa) | Filtrar todas las filas y calcular conteo, suma y mediana. |
| [D23_closure_actualizada](dificiles/D23_closure_actualizada.arepa) | Definir una función y comprobar que ve la reasignación de base. |
| [D24_recursion_suma](dificiles/D24_recursion_suma.arepa) | Sumar los enteros de 1 a 10 con caso base. |
| [D25_normalizacion_pipeline](dificiles/D25_normalizacion_pipeline.arepa) | Quitar duplicados, eliminar vacíos, convertir y resumir. |
