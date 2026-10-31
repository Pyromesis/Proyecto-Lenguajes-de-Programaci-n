# AREPA — Informe de la Fase 3: Visualización y producto final

**Proyecto:** Lenguaje de dominio específico para ciencia de datos y visualización
**Curso:** Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2
**Fase entregada:** Corte 3 — Visualización y producto final (acumulativa sobre los Cortes 1 y 2)
**Versión del intérprete:** `AREPA v0.4 (Fase 3 - visualizacion y producto final)`

---

## 1. Propósito

Este informe documenta el tercer corte del proyecto: cerrar el recorrido del
lenguaje con la **visualización**. Hasta el Corte 2 AREPA cargaba, preparaba,
agrupaba y exportaba datos a CSV, pero `pinte` solo se reconocía y validaba.
La Fase 3 convierte esa instrucción en un **motor gráfico propio** que dibuja
cinco tipos de gráfica y los exporta a PNG, sin matplotlib ni ninguna otra
biblioteca de dibujo, y lo demuestra con un **caso de estudio con datos
públicos** reproducibles.

El propósito de la fase, según el enunciado (`docs/Proyecto_LP.pdf`, sección 5), es:

1. al menos **cuatro tipos de gráficas configurables desde el DSL**;
2. **exportación a PNG**;
3. **CLI estable** con ejecución por consola;
4. **caso de estudio con datos reales**;
5. **manuales**, **pruebas de regresión** y **documentación**.

Este documento describe cómo quedó cada punto y dónde verificarlo.

---

## 2. Alcance implementado

| Alcance exigido | Estado | Dónde |
|---|---|---|
| Al menos 4 tipos de gráfica | **5 implementados**: `barras`, `lineas`, `histograma`, `dispersion`, `cajas` | `src/graficas/tipos_grafica.py` (`TIPOS`, línea 54) |
| Configuración desde el DSL | `titulo`, `ejex`, `ejey` (una columna o `[lista]`), `leyenda` | `gramatica/Arepa.g4:237` (`clausula_estetica`), `src/runtime/ejecutor.py:502` |
| Exportación a PNG | `guardela "ruta.png"` (PNG RGB 800x480) y `muestrela` | `src/graficas/png.py`, `src/runtime/ejecutor.py:847` |
| Ejecución por consola | `--ejecutar` y `--sin-ventana`; `--ayuda/--help/-h` y `--version` | `src/cli/main.py` (`main`, línea 121) |
| Caso de estudio con datos públicos | AirPassengers 1949-1960 (144 filas) + 5 PNG + CSV | `caso_estudio/` |
| Pruebas de regresión | 170 programas (164 ejercicios por corte + 6 ejemplos) con `--ejecutar` | `ejercicios/`, `ejemplos/` |
| Manuales y documentación | Manual de usuario y manual técnico; informes y matriz del corte | `docs/manuales/usuario.md`, `docs/manuales/tecnico.md`, este documento y `docs/12_matriz_trazabilidad_corte3.md` |

Todo el motor gráfico vive en `src/graficas/` y no importa ninguna biblioteca
externa: solo `math`, `os`, `struct` y `unicodedata` de la biblioteca estándar.

---

## 3. Arquitectura del motor gráfico

El motor se organiza en cinco módulos con una dependencia clara, de abajo
hacia arriba: `png` y `fuente` → `lienzo` → `escalas` → `tipos_grafica`.

```text
src/graficas/
├── png.py             codificador PNG propio (CRC-32, Adler-32, DEFLATE fijo + LZ77)
├── fuente.py          fuente bitmap 5x7 con un glifo por carácter ASCII imprimible
├── lienzo.py          búfer RGB y primitivas (píxel, línea, rectángulo, círculo, texto)
├── escalas.py         EscalaLineal / EscalaBanda, ticks "bonitos" y formato legible
└── tipos_grafica.py   Serie, Grafica y los cinco dibujos + cuartiles y cubetas
```

### 3.1 PNG propio (`png.py`)

Es el módulo de más bajo nivel y el que hace posible el "sin matplotlib".
Implementa el formato PNG **completo en lo mínimo necesario**:

* **Firma y chunks.** Escribe la firma `\x89PNG\r\n\x1a\n` y los chunks
  `IHDR`, `IDAT` e `IEND` (`png.py:456`, `_chunk`). Cada chunk lleva su
  longitud, su tipo, sus datos y su **CRC-32** calculado con una tabla propia
  (`crc32`, línea 78; `_construir_tabla_crc`, línea 61).
* **Cabecera.** `IHDR` fija profundidad 8, color RGB (tipo 2), compresión 0,
  filtro 0 y entrelazado 0 (`codificar_png`, línea 523).
* **Filtros.** Antepone el byte de filtro 0 (None) a cada fila de píxeles
  (`_armar_scanlines`, línea 507).
* **DEFLATE + zlib.** Comprime con LZ77 + Huffman **fijo** (BTYPE=01) en el
  modo por defecto (`_comprimir_fijo`, línea 392) y con **bloques guardados**
  (BTYPE=00) en el modo alternativo (`_comprimir_guardado`, línea 418), y
  envuelve el flujo con la cabecera y la **suma Adler-32** de zlib
  (`adler32`, línea 94; `_envolver_deflate`, línea 447). El LZ77 es voraz con
  hash exacto de 3 bytes y una cadena de hasta 64 candidatos (`_BuscadorLz77`,
  línea 322).
* **Escritura y lectura.** `escribir_png` (línea 561) crea las carpetas que
  falten y devuelve el tamaño; `leer_cabecera` (línea 577) permite validar el
  ancho, el alto y el tipo de un PNG ya codificado.

### 3.2 Lienzo (`lienzo.py`)

Es la superficie de dibujo: un `bytearray` RGB con el que se rasteriza a mano.
La clase `Lienzo` (línea 100) ofrece `poner`, `linea` (Bresenham, con grosor
por sello cuadrado, línea 160), `rectangulo` (línea 191), `rectangulo_relleno`
(línea 202), `circulo_relleno` (por filas con `math.isqrt`, sin coma flotante,
línea 209) y `texto` (línea 255). Los rellenos escriben por franjas con
asignación de *slices*. Todo trazo se recorta contra los bordes: `poner` fuera
del lienzo se ignora en silencio y nunca lanza `IndexError`. Se entrega como
`bytes` con `pixeles` (línea 287) o codificado a PNG con `guardar` (línea 297).

### 3.3 Fuente 5x7 (`fuente.py`)

El texto de las gráficas se dibuja con una **fuente bitmap propia**: un glifo
por cada carácter ASCII imprimible (32..126), de 7 filas de 5 bits
(`ANCHO = 5`, `ALTO = 7`, `SEPARACION = 1`). `normalizar_texto` (línea 220)
lleva el texto a ASCII imprimible con `unicodedata` (NFD) para quitar tildes y
diéresis, más un mapa propio (`_ESPECIALES`) para los signos que no se
descomponen (¿, ¡, rayas, comillas tipográficas). Cualquier carácter no
representable usa el glifo `?`, de modo que una etiqueta con emojis nunca
rompe el dibujo.

### 3.4 Escalas (`escalas.py`)

Traducen valores del dominio a píxeles y eligen las marcas de los ejes:

* `EscalaLineal` (línea 154): mapeo afín `dominio → rango`, su inverso y
  `ticks` con pasos "bonitos" de la forma 1, 2 o 5 por una potencia de diez
  (`paso_bonito`, línea 92). Un dominio degenerado se expande para no dividir
  por cero.
* `EscalaBanda` (línea 226): reparte categorías en bandas iguales y mapea cada
  una al centro de su banda (lo que necesitan barras y cajas).
* `formatear` (línea 119): convierte un número en etiqueta legible (enteros
  sin decimales; el resto con 1 o 2).

### 3.5 Tipos de gráfica (`tipos_grafica.py`)

Es el nivel más alto: define `Serie` (línea 274) y `Grafica` (línea 400), y la
función de conveniencia `dibujar(tipo, series, **opciones)` (línea 1058).
Comparte el marco de todas las gráficas: márgenes fijos
(`MARGEN_IZQUIERDO = 78`, `MARGEN_DERECHO = 24`, `MARGEN_SUPERIOR = 64`,
`MARGEN_INFERIOR = 64`), título centrado, nombre de los ejes, rejilla
horizontal suave, ticks con etiquetas y leyenda arriba a la derecha cuando hay
más de una serie. Los cinco dibujos son métodos privados
(`_dibujar_barras`, `_dibujar_lineas`, `_dibujar_histograma`,
`_dibujar_dispersion`, `_dibujar_cajas`) y el lienzo final se produce en
`renderizar` (línea 1046).

La estadística también es propia y verificable sin mirar píxeles:
`cuartiles` (línea 326) interpola Q1, Q2 y Q3 por posición; `cubetas_histograma`
(línea 355) calcula 5 a 20 cubetas según `sqrt(n)`.

---

## 4. Decisiones de diseño y limitaciones

| # | Decisión | Justificación | Limitación que implica |
|---|---|---|---|
| F1 | **PNG RGB 800x480 fijo** | Tamaño previsible y reproducible; suficiente para una figura de informe | No hay tamaño configurable ni salida vectorial |
| F2 | **DEFLATE fijo + LZ77 propio** | Gana compresión frente a bloques guardados y evita implementar Huffman dinámico | El modo "guardado" (BTYPE=00) sigue disponible como alternativa rápida y depurable; no se implementan bloques dinámicos (BTYPE=10) |
| F3 | **Sin antialiasing** | Bordes duros a propósito: PNG pequeño, resultado determinista y fácil de comparar por hash | Las líneas diagonales y los círculos muestran dentado |
| F4 | **Fuente 5x7 con tildes simplificadas** | Un glifo por carácter, sin dependencias ni fuentes del sistema | Las letras con tilde se dibujan sin ella (NFD); no hay descendentes reales (g, p, q, y, j) por la altura de 7 filas |
| F5 | **Un solo bloque DEFLATE final** | El formato no impone límite de tamaño a un bloque de Huffman; simplifica el codificador | El flujo entero se comprime y se emite en una pasada |
| F6 | **Sin escalas logarítmicas ni de fechas** | El caso de estudio no las necesita; las fechas se grafican como texto o como índice continuo | Un eje con escala logarítmica no es posible todavía |
| F7 | **Recorte de etiquetas con `...`** | El texto se dibuja horizontal y no se rota | Etiquetas largas se abrevian |
| F8 | **`muestrela` escribe siempre el archivo** | Garantiza evidencia en disco aunque no haya entorno gráfico | La apertura del visor es best-effort (ver §5) |

Limitaciones adicionales del motor: solo profundidad 8, color RGB y
entrelazado 0; los filtros 1-4 del PNG no se implementan (se usa siempre el
filtro 0); la cadena de candidatos del LZ77 es acotada (64), de modo que en
patrones muy ambiguos puede elegirse una coincidencia algo más corta que la
óptima, nunca una inválida.

---

## 5. Integración con el runtime y la CLI

La instrucción `pinte` la ejecuta `EjecutorArepa.visitInstruccion_grafica`
(`src/runtime/ejecutor.py:502`). El flujo es:

```text
pinte TIPO TABLA
  ├─ valida que la variable exista (ErrorVariable) y que la tabla no esté vacía (ErrorGrafica)
  ├─ lee las cláusulas: titulo, leyenda, ejex, ejey (columna o lista)
  ├─ aplica los VALORES POR DEFECTO de las columnas (§5.1)
  ├─ valida que cada columna de 'ejey' sea numérica (ErrorGrafica)
  ├─ construye una Serie por columna de 'ejey' y llama a dibujar(tipo, series, 800, 480)
  ├─ cierra con 'guardela' o 'muestrela'
  │    ├─ guardela: exige que la ruta termine en '.png' y escribe el archivo
  │    └─ muestrela: escribe 'salidas/<tabla>_<tipo>.png' y, si hay entorno
  │                  gráfico y no está AREPA_SIN_VENTANA, abre el visor
  └─ registra el archivo en el contexto (ruta, tipo 'png', bytes)
```

El registro de archivos es lo que permite que la CLI imprima al final el
bloque `Archivos generados:` con la ruta, el tipo y los bytes
(`src/cli/main.py:105`, `_resumen_archivos`).

### 5.1 Valores por defecto de las columnas

Documentados también en el docstring de `visitInstruccion_grafica`:

* **`ejex`**: la primera columna de tipo texto o fecha; si no hay ninguna, se
  usan los índices de fila 1..n como x numérica.
* **`ejey`**: todas las columnas numéricas de la tabla.
* **`histograma`**: exige exactamente una columna en `ejey` e **ignora
  `ejex`**, porque las cubetas se calculan sobre los valores de y.
* **`dispersion` sin `ejex`**: la primera columna numérica es x y las
  restantes son las series y; si solo hay una numérica, se usa como y y x pasa
  a ser el índice de fila.
* **`cajas`**: el motor **agrupa una caja por valor de `ejex`** cuando sus
  valores se repiten (sean texto o número); si cada x es única, hay una caja
  por serie de `ejey`. Los bigotes son 1.5 * IQR recortados a los datos y los
  valores fuera se dibujan como puntos atípicos.

### 5.2 CLI

El vocabulario del CLI en la versión final es:

| Opción | Efecto |
|---|---|
| `--ayuda` / `--help` / `-h` | Muestra la ayuda y sale (código 0) |
| `--version` | Imprime `AREPA v0.4 (Fase 3 - visualizacion y producto final)` |
| `--arbol` | Imprime el árbol de análisis |
| `--tokens` | Imprime la tabla de tokens |
| `--ejecutar` | Interpreta el programa con la biblioteca propia |
| `--sin-ventana` | No abre visores externos; equivale a `AREPA_SIN_VENTANA=1` |

Los errores se reportan con **línea, columna y un caret `^`** que señala la
posición. Los códigos de salida son 0 (válido), 1 (con errores) y 2 (archivo no
encontrado).

### 5.3 `guardela` vs `muestrela`

* `guardela "ruta.png"`: escribe exactamente en la ruta indicada; si la ruta no
  termina en `.png` se lanza `ErrorGrafica` (`ejecutor.py:713`).
* `muestrela`: escribe en `salidas/<tabla>_<tipo>.png` y solo abre el visor si
  hay entorno gráfico y no está definida `AREPA_SIN_VENTANA`
  (`_abrir_grafica`, `ejecutor.py:863`). Sin entorno gráfico imprime
  `[pinte] No hay entorno grafico; la imagen quedo en '...'`.

`pinte` sin cláusula final solo valida y renderiza, sin escribir archivo.

---

## 6. Caso de estudio

El caso de estudio cierra el recorrido con un flujo completo sobre datos
públicos: la serie mensual **AirPassengers** (pasajeros internacionales en
miles, 1949-1960), con 144 observaciones.

* Programa: `caso_estudio/programa.arepa` (flujo comentado: carga, limpieza,
  columna `periodo`, columna `decada` con etiqueta legible, resumen anual,
  indicadores y cinco gráficas).
* Datos: `caso_estudio/datos/pasajeros.csv` (144 filas), con su origen y
  transformación en `caso_estudio/datos/FUENTE.md`.
* Evidencia: `caso_estudio/salidas/pasajeros_por_anio.csv` y cinco PNG.

Reproducción desde la raíz:

```bash
AREPA_SIN_VENTANA=1 .venv/bin/python src/cli/main.py caso_estudio/programa.arepa --ejecutar
```

Indicadores verificados de la ejecución:

| Indicador | Valor |
|---|---:|
| Registros limpios | 144 |
| Total pasajeros | 40363 |
| Promedio mensual | 280.2986 |
| Mediana mensual | 265.5 |
| Mínimo mensual | 104 |
| Máximo mensual | 622 |
| Total 1949 | 1520 |
| Total 1960 | 5714 |
| Crecimiento 1949 → 1960 | 275.92 % |
| CAGR | 12.79 % |

Las cinco visualizaciones son `01_serie.png` (líneas sobre `periodo`),
`02_barras.png` (total anual), `03_histograma.png` (distribución de los 144
meses), `04_dispersion.png` (periodo frente a pasajeros) y `05_cajas.png`
(cajas por década).

**Nota sobre las cajas.** El motor agrupa por x repetida. El caso usa
etiquetas `"1940s"`, `"1950s"` y `"1960s"` (calculadas con la función
`rotulo_decada`), de modo que hay tres cajas. El eje x de la serie cubre
1949-1960 (el dominio real de los datos), no 1945-1965.

El análisis completo, con interpretación y discusión, está en
`caso_estudio/README.md`.

---

## 7. Resultados de las pruebas

La suite completa es el corredor `pruebas/test_proyecto.py` y su conteo único
está en `herramientas/chequeo_pruebas.py`:

```bash
.venv/bin/python herramientas/chequeo_pruebas.py
# Unificado: 8 suites, 319 pruebas.
```

| Suite | Archivo | Pruebas |
|---|---|---:|
| Front-end (léxico y sintáctico) | `test_front.py` | 55 |
| Estructura del árbol de análisis | `test_arbol.py` | 28 |
| Biblioteca propia de datos | `test_datos.py` | 43 |
| Estructuras propias (listas, registros, tablas) | `test_estructuras.py` | 48 |
| Evaluador de expresiones propio | `test_expresiones.py` | 16 |
| Tabla de símbolos y contexto propios | `test_simbolos.py` | 15 |
| Runtime propio (programas completos) | `test_runtime.py` | 51 |
| Motor gráfico y visualización propia | `test_graficas.py` | 63 |
| **Total** | | **319** |

El desglose del front-end, ahora en 55, es 10 positivos, 22 negativos, 10 de
diagnóstico y 13 de CLI.

La suite nueva, `pruebas/test_graficas.py` (63), se agrupa así: 20 casos del
codificador PNG (firma y chunks, CRC-32 y Adler-32, round-trips y errores),
3 de la fuente, 7 del lienzo, 4 de las escalas, 14 de los cinco dibujos y las
regresiones de ejes, 11 de integración con el runtime (`pinte` desde el DSL) y
4 del caso de estudio (ejecución, cinco PNG y el CSV, indicadores y
determinismo).

---

## 8. Regresión

Además de las suites, todo el corpus de programas se valida y ejecuta:

* **170 programas de regresión**: 164 ejercicios de `ejercicios/` (32 del
  Corte 1, 120 del Corte 2 y 12 del Corte 3) más los 6 ejemplos de `ejemplos/`.
* Todos pasan `--ejecutar` sin fallos, incluido `ejemplos/graficas.arepa`, que
  ahora **genera cinco PNG reales** en `salidas/` (no solo validación).
* `herramientas/chequeo_gramatica.py` confirma que la especificación EBNF sigue
  sincronizada con el `.g4`: 57 reglas y 65 palabras reservadas.
* `herramientas/regresion_programas.sh` ejecuta los 170 programas con
  `--ejecutar --sin-ventana` y falla si alguno no termina con código 0.
* `herramientas/demo_sustentacion.sh` recorre la evidencia completa y termina
  con `De una: demo de sustentación completa sin tropiezos.`

La regresión de los cortes anteriores se conserva: las dos regresiones
históricas (el pipeline en `cuenteme` y la precedencia `-2 ^ 2 = -4`) siguen
cubiertas por `test_estructuras.py`.

---

## 9. Evidencias generadas

| Evidencia | Qué demuestra | Ruta |
|---|---|---|
| 5 PNG del ejemplo | Los cinco tipos de gráfica desde el DSL | `salidas/barras.png`, `salidas/ventas_lineas.png`, `salidas/histograma.png`, `salidas/dispersion.png`, `salidas/cajas.png` |
| CSV del ejemplo | Exportación de resultados en paralelo a las gráficas | `salidas/*.csv` |
| 5 PNG + 1 CSV del caso | Flujo completo reproducible sobre datos públicos | `caso_estudio/salidas/` |
| Corredor de pruebas | 8 suites, 319 pruebas | `.venv/bin/python pruebas/test_proyecto.py` |
| Chequeo de conteo | Conteo único de pruebas | `.venv/bin/python herramientas/chequeo_pruebas.py` |
| Chequeo de gramática | EBNF ↔ `.g4` | `python3 herramientas/chequeo_gramatica.py` |
| Chequeo de documentación | Enlaces, referencias de código, rutas antiguas y conteos por corte | `python3 herramientas/chequeo_documentacion.py` |
| Demo de sustentación | Evidencia paso a paso, de punta a punta | `bash herramientas/demo_sustentacion.sh` |

Los PNG del caso de estudio son deterministas: dos ejecuciones consecutivas
producen los mismos `sha256sum`.

---

## 10. Conclusiones

1. **Se cumplió el alcance del Corte 3:** hay cinco tipos de gráfica
   configurables desde el DSL (más del mínimo de cuatro), exportación PNG con
   motor propio, CLI estable, caso de estudio con datos públicos, manuales,
   pruebas de regresión y documentación.
2. **Sigue vigente la regla del curso:** toda la lógica es propia. El motor
   gráfico implementa PNG, DEFLATE, LZ77, rasterizado y la estadística de las
   cajas sin pandas, NumPy ni Matplotlib. La única dependencia externa del
   proyecto sigue siendo ANTLR4, exigida por el enunciado para el lexer y el
   parser.
3. **La gramática no cambió de fondo:** el vocabulario de `pinte` ya estaba en
   el `.g4` desde el Corte 1, y en el Corte 3 sólo se afinó `clausula_estetica`
   para admitir `ejey` con lista (`EJEY NL* (nombre_columna | lista_literal)`),
   que habilita varias series. La sincronía EBNF ↔ ANTLR se mantiene en 57
   reglas y 65 reservadas.
4. **El proyecto quedó reproducible:** versiones, dependencias, comandos de
   verificación y evidencias están documentados y se pueden rehacer desde cero.

### Trabajo futuro

* Escalas logarítmicas y de fechas reales.
* Tamaño de figura configurable y filtros PNG 1-4.
* Huffman dinámico (BTYPE=10) para mejorar la compresión.
* Gráficas apiladas y eje secundario.
