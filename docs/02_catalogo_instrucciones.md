# AREPA — Catálogo de instrucciones y decisiones de diseño (Fase 1)

Aquí está el vocabulario completo de AREPA: palabras reservadas, operadores,
literales, sentencias y la razón de cada decisión que tomamos. La gramática
ejecutable correspondiente está en `gramatica/Arepa.g4`.

---

## 1. Filosofía del vocabulario

Las palabras reservadas de AREPA salen del **español hablado en Colombia**.
Escogimos cada palabra por ser coloquial, corta y fácil de recordar, y porque
lo que significa en el día a día se parece a lo que hace la instrucción:

| Palabra | Uso coloquial colombiano | Instrucción en AREPA |
|---|---|---|
| `quihubo` | saludo ("¿qué hubo?") | abre el programa |
| `chao` | despedida | cierra el programa |
| `monte` | "montar los datos" | carga un CSV |
| `guarde` / `guardela` | "guarde pues" | exporta tabla / gráfica |
| `escoja` | "escoja lo que necesita" | selecciona columnas |
| `deje donde` | "deje solo los que…" | filtra filas |
| `acomode` | "acomode eso" | ordena |
| `pa_arriba` / `pa_abajo` | "pa' arriba, pa' abajo" | orden ascendente/descendente |
| `cree` | "créeme una columna" | columna calculada |
| `renombre` | cambiar nombre | renombra columna |
| `limpie` | "limpie eso" | quita duplicados o vacíos |
| `convierta` | convertir | conversión de tipos |
| `junte por` | "júntelos por ciudad" | agrupamiento |
| `resuma` | "resuma" | agregaciones |
| `cuenteme` | "cuénteme, ¿qué salió?" | imprime valores |
| `describa` | "descríbame la tabla" | resumen estadístico |
| `pinte` | "pínteme esa gráfica" | visualización |
| `invente` | "invente una función" | define funciones |
| `devuelva` | retorno | valor de retorno |
| `fijese_si` | "fíjese si…" | condicional |
| `sino` | camino alterno | else |
| `obvio` | "¡obvio!" | verdadero |
| `falso` | negación absoluta | falso |
| `nada` | "no hay nada" | valor faltante |
| `y` | "a y b" | conjunción lógica |
| `o` | "a o b" | disyunción lógica |
| `no` | "no pasa" | negación lógica |

Con estas últimas, el vocabulario reservado queda en **51 palabras**: 45
instrucciones y estructuras, 3 literales especiales (`obvio`, `falso`,
`nada`) y 3 operadores lógicos (`y`, `o`, `no`).

**Decisión D1 — sin tildes en palabras reservadas.** Se escriben sin tilde
(`numero`, `lineas`, `titulo`) para no pelear con la codificación y porque así
es como se escribe normalmente en un chat. Los **identificadores** sí admiten
tildes, ñ y letras Unicode (`[\p{L}_][\p{L}\p{N}_]*`).

**Decisión D2 — minúscula estricta.** Las palabras reservadas son minúsculas;
los identificadores distinguen mayúsculas.

### 1.1 Colisiones léxicas: reservada vs identificador vs columna

La regla de precedencia léxica es: **si un lexema coincide con una palabra
reservada, el lexer produce el token reservado; solo si no coincide produce
`ID`**. De ahí salen tres reglas de nombres:

| Nombre | ¿Puede ser reservada? | Ejemplo | Resultado |
|---|---|---|---|
| Variable del programa | NO | `y = 5` | rechazado con pista ("'y' es una palabra reservada") |
| Identificador parecido | SÍ (si el lexema completo no es reservado) | `numerito = 1`, `y2 = 3` | válido: `numerito` y `y2` son `ID` |
| Columna de datos | SÍ | `escoja [fecha, ciudad]` | válido: las columnas vienen de CSV externos (decisión D5), la regla `nombre_columna` las acepta |

Ejemplos verificables: `pruebas/positivos/03_seleccion_filtro.arepa` (columna
`fecha`, que también es tipo reservado), `pruebas/positivos/08_casos_borde.arepa`
(identificadores con tilde y ñ) y `pruebas/negativos/n11_reservada_como_variable.arepa`
(variable `y` rechazada con explicación).

---

## 2. Estructura obligatoria de un programa

```text
# comentario inicial opcional
quihubo
  <sentencias>
chao
```

* `quihubo` y `chao` van cada uno en su propia línea; el salto después de
  `quihubo` es obligatorio.
* Comentarios con `#` hasta fin de línea; se permiten en cualquier posición
  del programa (antes de `quihubo`, entre sentencias y antes de `chao`).
* Cada sentencia termina en salto de línea.
* Continuación de línea permitida tras `|>`, tras coma, tras operador binario
  y dentro de `( )` y `[ ]`.

---

## 3. Palabras reservadas por componente

### 3.1 Carga y almacenamiento

| Sentencia | Sintaxis | Ejemplo |
|---|---|---|
| Cargar CSV | `ID = monte CADENA (con OPCIONES)?` | `ventas = monte "datos/v.csv" con encabezado obvio, separador ";"` |
| Guardar CSV | `guarde ID como CADENA` | `guarde resumen como "salidas/r.csv"` |

Opciones de carga: `encabezado` (+ `obvio`/`falso` opcional), `separador CADENA`.

### 3.2 Selección y preparación (etapas de pipeline)

| Etapa | Sintaxis | Ejemplo |
|---|---|---|
| Seleccionar columnas | `escoja [COL, …]` | `\|> escoja [fecha, ciudad]` |
| Filtrar filas | `deje donde EXPR_LÓGICA` | `\|> deje donde unidades > 0 y precio > 0` |
| Ordenar | `acomode (por)? [COL, …] (pa_arriba\|pa_abajo)?` | `\|> acomode por [precio] pa_abajo` |
| Renombrar | `renombre COL -> NUEVA` | `\|> renombre categoria -> cat` |
| Columna calculada | `cree COL = EXPR` | `\|> cree total = unidades * precio` |
| Limpiar duplicados | `limpie duplicados` | `\|> limpie duplicados` |
| Tratar vacíos | `limpie vacios (CON VALOR)?` | `\|> limpie vacios con 0` |
| Convertir tipo | `convierta COL -> TIPO` | `\|> convierta fecha -> fecha` |

Tipos: `numero`, `texto`, `logico`, `fecha`.

### 3.3 Transformación y análisis

| Etapa | Sintaxis | Ejemplo |
|---|---|---|
| Agrupar | `junte por [COL, …]` | `\|> junte por [ciudad]` |
| Agregar | `resuma ALIAS = AGREG(ARGS), …` | `\|> resuma ingreso = sume(total), n = cuente()` |

Funciones de agregación (identificadores predefinidos, no reservadas):
`cuente()`, `sume(col)`, `promedie(col)`, `mediana(col)`, `minimo(col)`,
`maximo(col)`, `desviacion(col)`.

Sentencia directa:

| Sentencia | Ejemplo |
|---|---|
| `describa ID` | resumen estadístico de la tabla |

### 3.4 Visualización (solo reconocimiento en Fase 1)

```text
pinte TIPO TABLA
  (titulo CADENA)? (ejex COL)? (ejey COL)? (leyenda CADENA)?
  (guardela CADENA | muestrela)?
```

TIPO ∈ { `barras`, `lineas`, `histograma`, `dispersion`, `cajas` }.

Ejemplo:

```text
pinte barras resumen
titulo "Ingresos por ciudad"
ejex ciudad
ejey ingreso
guardela "salidas/ingresos.png"
```

### 3.5 Abstracción y control

| Constructo | Sintaxis |
|---|---|
| Función | `invente NOMBRE(P, …) { sentencias }` |
| Retorno | `devuelva EXPR?` |
| Condicional | `fijese_si (EXPR) { … } sino { … }` (el `sino` puede encadenar otro `fijese_si`) |
| Impresión | `cuenteme ARG, ARG, …` |

---

## 4. Operadores

| Clase | Operadores | Notas |
|---|---|---|
| Aritméticos | `+  -  *  /  %  ^` | `^` es potencia, asociativa a derecha |
| Relacionales | `==  !=  <  <=  >  >=` | producen lógicos |
| Lógicos | `y   o   no` | palabras, no símbolos |
| Asignación | `=` | solo sentencia |
| Encadenamiento | `\|>` | pipeline de etapas sobre tablas |
| Renombre/conversión | `->` | flecha |
| Agrupación | `( )  [ ]  { }` | expresiones, listas de columnas, bloques |

**Precedencia** (menor a mayor): `o` < `y` < `no` < comparaciones < `+ -` <
`* / %` < `-` unario < `^`. Paréntesis alteran el orden.

---

## 5. Literales

| Tipo | Forma | Ejemplos |
|---|---|---|
| Entero | dígitos | `0`, `42` |
| Decimal | dígitos punto dígitos | `3.14` |
| Cadena | entre comillas dobles, con escapes `\n \t \\ \"` | `"Bogotá"` |
| Lógico | `obvio`, `falso` | |
| Faltante | `nada` | |

---

## 6. El pipeline `|>`

**Decisión D3 — estilo declarativo de encadenamiento.** Siguiendo la propuesta
del enunciado del curso, cada operación recibe una tabla y devuelve otra
nueva, sin modificar la que entra:

```text
limpias = ventas
|> escoja [ciudad, unidades, precio]
|> deje donde unidades > 0
|> cree total = unidades * precio
```

El `|>` puede abrir línea para que el programa se lea como una receta de
cocina: una etapa por línea.

---

## 7. Decisiones de diseño relevantes

| # | Decisión | Justificación |
|---|---|---|
| D4 | Saltos de línea significativos | Delimitan sentencias sin `;`; imitan el ejemplo del enunciado |
| D5 | `nombre_columna` acepta cualquier palabra reservada | Los nombres de columnas vienen de CSV externos que AREPA no controla (una columna puede llamarse `fecha` o `total`); las variables del programa sí exigen identificador puro |
| D6 | Agregaciones como identificadores predefinidos, no reservadas | Reduce el vocabulario reservado y permite usarlas como llamadas uniformes dentro de `resuma` y expresiones |
| D7 | Condicionales y funciones desde la Fase 1 en la gramática | El alcance del corte exige asignaciones/expresiones/filtros/gráficas, pero diseñar todo el catálogo desde ya evita romper sintaxis en fases futuras |
| D8 | `pinte` es sentencia, no expresión | Una gráfica no compone aritméticamente; separarla simplifica la gramática y su semántica futura |
| D9 | Sin acceso con punto (`tabla.columna`) | En el pipeline la tabla implícita es la etapa anterior; el punto queda como ampliación |
| D10 | Errores en español con línea y columna | Requisito del componente "Errores y diagnóstico"; mejora la comprensibilidad |

---

## 8. Programa de referencia

Ver `ejemplos/demo.arepa`: carga, preparación en pipeline, resumen por ciudad,
condicional, función inventada, gráfica de barras exportada a PNG y guardado CSV.
