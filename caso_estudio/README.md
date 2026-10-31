# Caso de estudio: pasajeros internacionales 1949-1960

Este caso cierra el recorrido de AREPA con un flujo completo y reproducible:
carga de un CSV real, limpieza, columnas calculadas, agregación anual,
indicadores y cinco gráficas exportadas como evidencia. Todos los resultados
de este documento salen de ejecutar `caso_estudio/programa.arepa` sobre
`caso_estudio/datos/pasajeros.csv`.

## 1. Descripción del conjunto y pregunta de análisis

El conjunto es la serie mensual **AirPassengers**: el número de pasajeros
internacionales, en miles, transportados por una aerolínea entre enero de 1949
y diciembre de 1960. Tiene 144 observaciones, una por mes, sin faltantes ni
duplicados. Su origen bibliográfico y la transformación aplicada están
documentados en [`datos/FUENTE.md`](datos/FUENTE.md).

La pregunta de análisis es:

> ¿Cómo evoluciona la demanda mensual de transporte aéreo entre 1949 y 1960 y
> qué papel juega la estacionalidad en esa evolución?

El interés del conjunto está en que combina dos patrones que conviene separar:
una **tendencia creciente** de largo plazo y un **ciclo anual** muy marcado.
Mirar solo el total anual esconde el ciclo; mirar solo un mes esconde la
tendencia.

## 2. Preguntas concretas

1. ¿Cuánto crece la demanda entre 1949 y 1960 y a qué ritmo medio anual?
2. ¿Hay estacionalidad? ¿En qué meses se concentran los máximos y los mínimos?
3. ¿Cómo se distribuyen los 144 valores mensuales: simétricos o sesgados?
4. ¿Cambia el nivel y la dispersión de la demanda al pasar de una década a otra?

## 3. Programa DSL

El programa completo está en [`programa.arepa`](programa.arepa). Se ejecuta
desde la raíz del repositorio con:

```bash
AREPA_SIN_VENTANA=1 .venv/bin/python src/cli/main.py caso_estudio/programa.arepa --ejecutar
```

Extracto del flujo (las cinco gráficas se detallan en la sección 6):

```text
quihubo

# Etiqueta legible de la década: "1940s", "1950s" o "1960s".
# El sufijo evita que la etiqueta se confunda con un valor numérico.
invente rotulo_decada(decada) {
    fijese_si (decada < 1950) {
        devuelva "1940s"
    }
    fijese_si (decada < 1960) {
        devuelva "1950s"
    }
    devuelva "1960s"
}

pasajeros = monte "caso_estudio/datos/pasajeros.csv" con encabezado, separador ","

preparada = pasajeros
|> escoja [anio, mes, pasajeros]
|> deje donde pasajeros > 0
|> cree periodo = anio + (mes - 1) / 12
|> cree decada = anio - (anio % 10)
|> cree decada_etiqueta = rotulo_decada(decada)
|> convierta decada -> texto
|> escoja [anio, mes, pasajeros, periodo, decada_etiqueta]
|> renombre decada_etiqueta -> decada

resumen = preparada
|> junte por [anio]
|> resuma total = sume(pasajeros),
   promedio = promedie(pasajeros),
   maximo_mes = maximo(pasajeros),
   registros = cuente()

p_1949 = preparada
|> deje donde anio == 1949

p_1960 = preparada
|> deje donde anio == 1960

cuenteme "Registros limpios:", cuente(preparada)
cuenteme "Total pasajeros:", sume(preparada, pasajeros)
cuenteme "Promedio mensual:", promedie(preparada, pasajeros)
cuenteme "Mediana mensual:", mediana(preparada, pasajeros)
cuenteme "Minimo mensual:", minimo(preparada, pasajeros)
cuenteme "Maximo mensual:", maximo(preparada, pasajeros)
cuenteme "Total 1949:", sume(p_1949, pasajeros)
cuenteme "Total 1960:", sume(p_1960, pasajeros)
cuenteme "Crecimiento 1949-1960 (%):", (sume(p_1960, pasajeros) - sume(p_1949, pasajeros)) / sume(p_1949, pasajeros) * 100

guarde resumen como "caso_estudio/salidas/pasajeros_por_anio.csv"
```

## 4. Limpieza y transformación

| Paso | Qué hace | Por qué |
|---|---|---|
| `monte ... con encabezado, separador ","` | Lee el CSV y toma la primera fila como nombres de columna. | El archivo local usa coma y encabezado `anio,mes,pasajeros`. |
| `escoja [anio, mes, pasajeros]` | Conserva solo las tres columnas de análisis. | Evita arrastrar columnas auxiliares al resumen y a las gráficas. |
| `deje donde pasajeros > 0` | Descarta meses sin pasajeros. | No hay ninguno en este conjunto, pero el filtro documenta la regla y hace robusto el flujo ante ceros o valores inválidos. |
| `cree periodo = anio + (mes - 1) / 12` | Convierte año y mes en un eje temporal continuo. | Permite dibujar la serie mensual y la dispersión sin perder el orden cronológico. |
| `cree decada = anio - (anio % 10)` | Calcula el año base de la década: 1940, 1950, 1960. | Es la variable de agrupación temporal gruesa. |
| `cree decada_etiqueta = rotulo_decada(decada)` | Convierte la década en `"1940s"`, `"1950s"` o `"1960s"`. | Da una etiqueta legible en el eje x y evita depender de la heurística numérica del motor. |
| `convierta decada -> texto` | Deja la década numérica como texto, según el flujo solicitado. | Conserva la representación textual de la variable antes de reemplazarla por la etiqueta legible. |
| `escoja [...]` y `renombre decada_etiqueta -> decada` | Quita la década numérica y deja la etiqueta con el nombre `decada`. | La gráfica de cajas usa literalmente `decada` y muestra tres cajas con la etiqueta `decada` en el eje x. |

El resultado de la limpieza son **144 filas** y cinco columnas:
`anio`, `mes`, `pasajeros`, `periodo` y `decada`.

## 5. Indicadores

Todos los valores se obtuvieron de la ejecución del programa y del resumen
anual exportado.

| Indicador | Valor |
|---|---:|
| Registros limpios | 144 |
| Total de pasajeros (miles) | 40 363 |
| Promedio mensual | 280.2986 |
| Mediana mensual | 265.5 |
| Mínimo mensual | 104 (noviembre de 1949) |
| Máximo mensual | 622 (julio de 1960) |
| Total 1949 | 1 520 |
| Total 1960 | 5 714 |
| Crecimiento absoluto 1949 → 1960 | 4 194 |
| Crecimiento relativo 1949 → 1960 | 275.92 % |
| Crecimiento medio anual compuesto (CAGR) | 12.79 % |
| Desviación típica muestral | 119.97 |

El promedio (280.30) es mayor que la mediana (265.5): la distribución tiene una
cola hacia los valores altos, coherente con el crecimiento de la serie.

## 6. Las cinco visualizaciones

Todas se generan con `guardela`, sin abrir ventana, para que la ejecución sea
reproducible en CI. Son PNG RGB de 800 × 480.

### 6.1 Serie mensual — `salidas/01_serie.png`

`pinte lineas` sobre `periodo` y `pasajeros`, con título
"Pasajeros internacionales 1949-1960".

Muestra la tendencia creciente y el ciclo anual. Cada año repite un patrón:
la demanda sube hacia julio-agosto y baja hacia noviembre. Al final de la
serie los picos superan los 600 mil pasajeros mensuales; al inicio rondan los
150 mil. El eje x cubre el dominio real de los datos (1949-1960) con un
margen mínimo, y las marcas caen en 1950, 1955 y 1960.

### 6.2 Barras por año — `salidas/02_barras.png`

`pinte barras` sobre la tabla `resumen`, con `ejex anio`, `ejey total` y título
"Pasajeros por año".

Cada barra es el total anual. La secuencia es estrictamente creciente:
1 520 en 1949, 2 867 en 1954, 4 572 en 1958 y 5 714 en 1960. La barra más alta
casi cuadruplica la primera, lo que resume el crecimiento del 275.92 %.

### 6.3 Histograma — `salidas/03_histograma.png`

`pinte histograma` sobre `pasajeros`, con título "Distribución mensual".

Agrupa los 144 valores en diez cubetas. La moda está en 147.2-190.3 (21 meses)
y la frecuencia decae hacia la derecha: solo unos pocos meses superan los 490
mil pasajeros. La forma es asimétrica a la derecha, no una campana simétrica.

### 6.4 Dispersión — `salidas/04_dispersion.png`

`pinte dispersion` sobre `periodo` y `pasajeros`, con título
"Tendencia y estacionalidad".

Cada punto es un mes. La nube asciende de izquierda a derecha y se abre en
abanico: en los años cincuenta la dispersión vertical es mayor que a finales
de los cuarenta. Esa heterocedasticidad (la variabilidad crece con el nivel)
sugiere un modelo multiplicativo, no aditivo.

### 6.5 Cajas por década — `salidas/05_cajas.png`

`pinte cajas` sobre `decada` y `pasajeros`, con título "Pasajeros por década".

Hay exactamente tres cajas: 1940s, 1950s y 1960s. Las medianas son 125, 265.5
y 461 respectivamente; también crecen el rango y la altura de la caja. La
década de 1960 es la más alta y la más compacta (390-622), mientras que la de
1950 concentra la mayor dispersión (114-559) porque contiene la transición de
la serie.

## 7. Interpretación de resultados

La demanda crece de forma sostenida: pasa de 1 520 mil pasajeros en 1949 a
5 714 mil en 1960, un aumento de 4 194 mil (275.92 %). El ritmo medio anual
compuesto es 12.79 %. El crecimiento no es lineal: se acelera en la segunda
mitad de la serie, sobre todo entre 1954 y 1956 y entre 1958 y 1960.

La estacionalidad es fuerte y estable. Julio y agosto concentran el 20.9 % de
todos los pasajeros-mes, con promedios de 351.3 y 351.1 mil; noviembre es el
valle, con 232.8 mil de promedio y el mínimo absoluto de 104 mil (noviembre de
1949). El pico de julio de 1960 (622 mil) es casi seis veces ese mínimo.

La distribución mensual es asimétrica a la derecha: la mayoría de los meses se
ubica entre 104 y 320 mil pasajeros, y solo los veranos de los últimos años
alcanzan la cola alta. La mediana (265.5) queda por debajo del promedio
(280.30), otra señal del peso de los valores extremos.

Las cajas por década resumen el cambio de régimen: mediana de 125 en los
cuarenta, 265.5 en los cincuenta y 461 en los sesenta. La dispersión también
aumenta con el nivel, lo que respalda la lectura de un proceso multiplicativo
(tendencia × estacionalidad). Un modelo aditivo subestimaría la variabilidad
de los años altos.

Estos resultados son descriptivos: con 12 años de datos no se pretende probar
causalidad ni pronosticar fuera de la muestra. El valor del caso está en
mostrar cómo un flujo declarativo en AREPA separa tendencia, estacionalidad y
distribución sin escribir código de análisis a mano.

## 8. Archivos generados y reproducción

Desde la raíz del repositorio:

```bash
AREPA_SIN_VENTANA=1 .venv/bin/python src/cli/main.py caso_estudio/programa.arepa --ejecutar
```

Salida esperada (código de salida 0):

```text
Análisis léxico   : OK (412 tokens)
Análisis sintáctico: OK
...
Registros limpios: 144
Total pasajeros: 40363
Promedio mensual: 280.2986111111111
Mediana mensual: 265.5
Minimo mensual: 104
Maximo mensual: 622
Total 1949: 1520
Total 1960: 5714
Crecimiento 1949-1960 (%): 275.92105263157896
[guarde] La tabla 'resumen' quedo escrita en 'caso_estudio/salidas/pasajeros_por_anio.csv' (12 filas).
[pinte] Grafica de lineas guardada en 'caso_estudio/salidas/01_serie.png' (13886 bytes, 800x480).
[pinte] Grafica de barras guardada en 'caso_estudio/salidas/02_barras.png' (13131 bytes, 800x480).
[pinte] Grafica de histograma guardada en 'caso_estudio/salidas/03_histograma.png' (11215 bytes, 800x480).
[pinte] Grafica de dispersion guardada en 'caso_estudio/salidas/04_dispersion.png' (12031 bytes, 800x480).
[pinte] Grafica de cajas guardada en 'caso_estudio/salidas/05_cajas.png' (10859 bytes, 800x480).
...
¡De una! El programa corrió completo sin tropiezos.
```

Archivos producidos:

| Archivo | Contenido | Tamaño |
|---|---|---:|
| `salidas/pasajeros_por_anio.csv` | 12 filas: `anio,total,promedio,maximo_mes,registros` | 398 B |
| `salidas/01_serie.png` | Serie mensual de pasajeros | 13 886 B |
| `salidas/02_barras.png` | Total anual por año | 13 131 B |
| `salidas/03_histograma.png` | Distribución de los 144 meses | 11 215 B |
| `salidas/04_dispersion.png` | Periodo frente a pasajeros | 12 031 B |
| `salidas/05_cajas.png` | Cajas por década | 10 859 B |

Verificación de integridad de las imágenes:

```bash
file caso_estudio/salidas/*.png
sha256sum caso_estudio/salidas/*
```

Las cinco imágenes son deterministas: dos ejecuciones consecutivas producen
los mismos SHA-256.

Pruebas de integración del caso:

```bash
.venv/bin/python pruebas/test_graficas.py       # 63 de 63
.venv/bin/python herramientas/chequeo_pruebas.py  # 8 suites, 319 pruebas
```

## 9. Estructura de la carpeta

```text
caso_estudio/
├── README.md                  # este documento
├── programa.arepa             # flujo DSL completo y comentado
├── datos/
│   ├── pasajeros.csv          # 144 filas: anio,mes,pasajeros
│   └── FUENTE.md              # origen, transformación, licencia y SHA-256
└── salidas/
    ├── pasajeros_por_anio.csv # resumen anual
    ├── 01_serie.png
    ├── 02_barras.png
    ├── 03_histograma.png
    ├── 04_dispersion.png
    └── 05_cajas.png
```
