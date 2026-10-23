# AREPA — Reglas semánticas (Cortes 2 y 3, Linux)

Documento dedicado del entregable "documentación de reglas semánticas".
Todo se verifica en Linux con:

```bash
python3 pruebas/test_proyecto.py
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
python3 src/cli/main.py ejemplos/memoria.arepa --ejecutar
python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar --sin-ventana
```

Referencia de implementación: `docs/05_arquitectura.md` (§2–§6.2),
`docs/02_catalogo_instrucciones.md` (§3.4, §3.6–§3.8, §4–§5),
`docs/08_informe_fase2.md` y `docs/11_informe_fase3.md`.

---

## 1. Modelo de valores

| Valor | Representación | Notas |
|---|---|---|
| número entero | `42` | aritmética binaria de Python |
| número decimal | `3.14` | `float`; `4.0` se exporta como `4` |
| texto | `"Bogotá"` | UTF-8; escapes `\\n \\t \\\\ \\" \\b \\r` |
| lógico | `obvio` / `falso` | únicos valores de condición |
| faltante | `nada` | estilo SQL: se propaga, nunca equivale |
| infinito | `infinito` / `-infinito` | solo como resultado de `1/0`, `-1/0`, desborde de `^` |
| lista | `Lista` | arreglo dinámico propio; literales `[1, 2]`, `[]` |
| registro | `Registro` | pares clave→valor en orden; literales `{nombre: "Ana"}`, `{}` |
| tabla | `Tabla` | columnas + filas; `monte` o `arme [col, …] con [[…]]` |

Conversión CSV → valor (`datos/tipos.py::texto_a_valor`): entero →
decimal → lógico (`obvio`/`falso`) → texto. Campo vacío → `nada`.

**Impresión (`runtime/contexto.py::a_texto`).** `cuenteme` usa el formato
propio: una lista se ve `[1, 2, 3]`, un registro `{nombre: "Ana", edad:
20}` (los textos internos van entre comillas) y una tabla usa
`Tabla.texto_tabla` con encabezado, separador y alineación por columna.
`nada` se muestra como `nada`; los lógicos como `obvio`/`falso`.

## 2. Expresiones y tipos (`expresiones/operadores.py`)

* `nada` se propaga: `nada + 1`, `nada == 5`, `obvio y nada` → `nada`.
* Comparaciones solo dentro del mismo género (número-número,
  texto-texto, lógico-lógico). Mezclar número con texto →
  `ErrorTipos`. Sin coerción número↔texto, sin concatenación con `+`.
* Lógicos exigen `obvio`/`falso`; `1 y obvio` → `ErrorTipos`.
* `1/0` → `infinito`, `-1/0` → `-infinito`, `0/0` → `nada`,
  `5%0` → `nada` (no tumban el runtime).
* `^` asociativa a derecha; `(-1) ^ 0.5` → `ErrorOperacion`
  (resultado complejo). Desborde → `infinito` con signo.
* Precedencia: `o` < `y` < `no` < comparación < `+ -` < `* / %` <
  `-` unario < `^` < acceso `[ … ]` < átomo. El paréntesis altera el
  orden. Por eso `-2 ^ 2` es `-(2 ^ 2) = -4` y `a[1] + 1` indexa antes
  de sumar. La cadena del `.g4` es `expresion_logica → conjuncion →
  negacion → comparacion → aritmetica → termino → unario → potencia →
  acceso → atomo`; `factor` ya no existe.

## 3. Nombres: variables vs columnas (`expresiones/evaluador.py`)

* Variable del programa: exige `ID` puro. Usar reservada (`y = 5`) →
  error sintáctico con pista.
* Columna de datos: acepta `ID` o cualquier reservada
  (`nombre_columna`, decisión D5) porque los encabezados vienen de
  CSV externos (`fecha`, `total`, …).
* Resolución `_resolver_nombre`: 1) columna de la fila en contexto,
  2) variable en `TablaSimbolos`, 3) `ErrorVariable` con columnas
  disponibles como pista. En modo agregación el nombre se pasa sin
  evaluar (`sume(precio)` recibe nombre, no valor).
* `modo_resuma` se activa solo mientras se evalúan los ítems de
  `resuma`; `modo_columna` devuelve el nombre tal cual. Fuera de
  `resuma`, las agregaciones evalúan el primer argumento como valor
  (tabla o lista) y el segundo como nombre de columna.

## 4. Tabla de símbolos y ámbitos (`runtime/simbolos.py`)

* Ámbitos encadenados hijo→padre. `declarar` escribe en el actual;
  `buscar`/`asignar` suben por la cadena.
* `x = valor` declara si no existe en ningún ámbito visible y asigna
  si existe (semántica tipo Python).
* Solo las funciones `invente` crean ámbito (closure con el ámbito de
  definición, permite recursión). `fijese_si`, los ciclos y `recorra` NO
  crean ámbito: la variable del rango `repita i desde…` y la del
  recorrido `recorra x en…` quedan visibles al terminar.
* Identificadores: letra Unicode (ñ, tildes) o `_` al inicio.

## 5. Pipeline de datos (`runtime/ejecutor.py`, `datos/tabla.py`)

* Cada etapa `|>` recibe una tabla y devuelve una NUEVA (D3: la
  entrada nunca se muta).
* Primera etapa: `monte` o valor evaluado. Toda etapa siguiente debe
  ser operación de datos; operar sin tabla de entrada →
  `ErrorOperacion`.
* `escoja [cols]`: toda columna debe existir, si no `ErrorColumna`.
* `deje donde COND`: conserva la fila solo si `COND` es exactamente
  `obvio`. `nada` o no-lógico descarta la fila (filtro) — pero en
  `fijese_si`/`mientras` el no-lógico es error (ver §7).
* `cree col = EXPR`: la columna no debe existir ya; evalúa por fila.
* `renombre A -> B`: `A` debe existir, `B` no debe existir.
* `acomode [cols]`: merge sort propio estable; `nada` siempre al
  final; dos `nada` son iguales (orden determinista).
* `limpie duplicados`: conserva primera aparición (clave = tupla);
  no admite `con VALOR` (→ `ErrorSemantico`).
  `limpie vacios con V`: rellena `nada` con `V`;
  `limpie vacios` solo: elimina filas con algún `nada`.
* `convierta COL -> tipo`: `numero`/`texto`/`logico`/`fecha`
  (fecha válida `AAAA-MM-DD` con bisiesto; si no, `ErrorTipos`).
* `junte por [cols]` + `resuma a = AGREG(...)`: agrupa conservando
  orden de primera aparición. El `junte` solo prepara el `resuma`
  inmediato: si otra operación se interpone, las claves rezagadas se
  descartan. Agregaciones:
  `cuente/sume/promedie/mediana/minimo/maximo/desviacion`
  (desviación poblacional). Los `nada` se ignoran; grupo vacío →
  `nada`. Dentro de `resuma` los argumentos son nombres de columna
  (`sume(total)`, `cuente()`); fuera de `resuma` se usan las formas
  `sume(tabla, columna)`, `sume(lista)`, `cuente(tabla)`,
  `cuente(tabla, columna)` y `cuente(lista)`. Sobre columna inexistente →
  `ErrorColumna`; sobre un primer argumento que no es tabla/lista →
  `ErrorTipos`.
* `describa TABLA`: resumen estadístico por columna numérica con las
  6 agregaciones; exige tabla.
* `monte RUTA`: lector propio UTF-8 (tolera BOM `utf-8-sig`), máquina
  de estados con comillas y `""`; fila con más campos que el
  encabezado o comillas sin cerrar → `ErrorCSV` con línea del
  archivo; con menos campos se rellena con `nada`. Archivo ausente o
  no UTF-8 → `ErrorArchivo`.
* `guarde TABLA como RUTA`: exige tabla; escritor propio UTF-8 sin
  BOM; crea la carpeta destino; entrecomilla si hay separador,
  comilla o salto. `guarde` sobre no-tabla → `ErrorOperacion`.

## 5.1 Estructuras en memoria (`Lista`, `Registro`, `Tabla`)

**Construcción.** `[ … ]` crea una `Lista`, `{clave: …}` un `Registro`
(las claves son `nombre_columna` o cadenas) y `arme [col, …] con [[…], …]`
una `Tabla`. `arme [col, …]` sin `con` crea una tabla vacía; cada fila de
`con` debe traer exactamente un valor por columna o se lanza `ErrorTipos`
con la fila (1-based). `[]` y `{}` son válidos.

**Acceso 1-based (D12).** `x[1]` es el primer elemento/fila/celda; `[0]`,
los negativos y los índices no enteros se rechazan. Las reglas por tipo:

| Contenedor | Índice | Resultado |
|---|---|---|
| `Lista` | entero 1..largo | elemento |
| `Tabla` | entero 1..filas | `Registro` enlazado de la fila |
| `Registro` | texto (clave) | valor; `ErrorColumna` si no existe |
| `Fila` | entero 1..columnas | celda |

El acceso se encadena (`gente[1]["edad"]`, `anidada[2][1]`) y el índice
puede ser cualquier expresión entera. Un índice fuera de rango produce
`ErrorOperacion` con el tamaño en numeración 1-based; un tipo no
indexable (`numero`, `texto`, `nada`) produce `ErrorTipos`.

**Asignación indexada y mutación (D13).** `x[i] = v` actualiza listas,
registros, celdas de fila y filas de tabla; en una tabla la parte derecha
puede ser una `Lista` (por posición) o un `Registro` (por nombre de
columna), y debe cubrir todas las columnas. La variable debe existir
(`ErrorVariable` si no). El pipeline **no muta**: cada etapa `|>` devuelve
una tabla nueva. Solo `agregue`, `saque` y la asignación indexada mutan
explícitamente la variable que reciben.

**`agregue EXPR en ID`.** En una `Lista` agrega al final. En una `Tabla`
agrega una fila; `EXPR` debe ser una `Lista`/`Fila` con tantos valores
como columnas o un `Registro` con todas las claves (`ErrorColumna` si
falta una, `ErrorTipos` si sobra/falta un valor o el destino no es
colección).

**`saque EXPR de ID`.** Quita la fila o el elemento en la posición
entera 1-based; fuera de rango → `ErrorOperacion`; posición no entera →
`ErrorTipos`; destino que no es tabla/lista → `ErrorTipos`.

**`recorra VAR en ID { … }`.** Recorre una `Tabla` (cada vuelta enlaza un
`Registro` de fila) o una `Lista` (cada vuelta recibe un elemento).
Toma una **instantánea** al empezar: `agregue`/`saque` durante el
recorrido no cambian las vueltas pendientes; asignar celdas sí se refleja
porque el registro de fila está enlazado. El bloque no crea ámbito, la
variable del recorrido queda visible al terminar, y `pare`/`siga`
funcionan como en los demás ciclos. Recorrer otro tipo → `ErrorTipos`.
El tope de 1 000 000 de vueltas también aplica.

**Agregaciones en memoria y builtins.** `sume(tabla, columna)`,
`sume(lista)`, `promedie`, `mediana`, `minimo`, `maximo`, `desviacion`
con las mismas dos formas; `cuente(tabla)`, `cuente(lista)` y
`cuente(tabla, columna)` (cuenta celdas no `nada`). Los `nada` se ignoran
y una colección sin valores produce `nada` (salvo `cuente` → 0).
`largo(x)` acepta tabla/lista/registro/texto; `columna(tabla, nombre)`
devuelve una `Lista`; `columnas(tabla)` devuelve una `Lista` de nombres.

## 6. Funciones (`invente` / `devuelva` / llamada)

* `invente f(params) {…}` registra `FuncionArepa` (cuerpo + closure).
* La llamada crea ámbito hijo, enlaza argumentos (número exacto, si
  no `ErrorEjecucion`), ejecuta el cuerpo.
* `devuelva EXPR?` interrumpe con señal interna `RetornoFuncion`;
  fuera de función → error semántico.
* Recursión sin caso base → `ErrorEjecucion` en español (no
  `RecursionError` crudo).

## 7. Control: condicional y ciclos

* `fijese_si (COND) {…} sino {…}`: `COND` debe ser `obvio`/`falso`;
  `nada` u otro tipo → `ErrorTipos`.
* `mientras (COND) {…}`: reevalúa por vuelta; misma regla lógica.
* `repita N veces {…}`: `N` se evalúa una vez, exige entero ≥ 0;
  `0` no ejecuta el cuerpo.
* `repita i desde A hasta B (paso P) {…}`: extremos inclusivos; paso
  por defecto `1` (o `-1` si `A > B`); paso `0` → error; el bloque
  no crea ámbito.
* `pare` sale del ciclo más cercano; `siga` salta a la siguiente
  vuelta (señales internas `SalirCiclo`/`SeguirCiclo`). Fuera de
  ciclo → error semántico.
* Tope de seguridad: > 1 000 000 de vueltas → `ErrorEjecucion` que
  pide revisar condición/rango/paso (no se cuelga).

## 8. Visualización (`pinte`, implementada desde la Fase 3)

`pinte TIPO TABLA [titulo] [ejex] [ejey] [leyenda] [cierre]`.

**Validaciones.** La tabla debe existir y tener filas (`ErrorGrafica` si está
vacía). Las columnas de `ejex`/`ejey` deben existir (`ErrorGrafica` que lista
las columnas disponibles); toda columna de `ejey` debe ser numérica
(`ErrorGrafica` con el tipo encontrado). `titulo`, `leyenda` y `ejey` no pueden
repetirse. Un tipo inválido (`pastel`) es error **sintáctico**.

**Tipos.** `barras`, `lineas`, `histograma`, `dispersion`, `cajas`
(`src/graficas/tipos_grafica.py`).

**Valores por defecto.**

* `ejex`: la primera columna de texto o fecha; si no hay, índices de fila 1..n.
* `ejey`: todas las columnas numéricas; con lista (`ejey [a, b]`) hay una serie
  por columna.
* `histograma`: exige exactamente una columna en `ejey` e **ignora `ejex`**.
* `dispersion` sin `ejex`: la primera columna numérica es x; si solo hay una
  numérica, x pasa a ser el índice de fila.
* `cajas`: agrupa **una caja por valor de `ejex`** cuando sus valores se
  repiten (sean texto o número); si cada x es única, una caja por serie de
  `ejey`. Los
  bigotes son 1.5 * IQR recortados a los datos y los valores fuera se dibujan
  como puntos atípicos.

**Cierre.**

* `guardela "ruta.png"`: exige que la ruta termine en `.png` (`ErrorGrafica` si
  no) y escribe el archivo.
* `muestrela`: escribe `salidas/<tabla>_<tipo>.png` y, solo si hay entorno
  gráfico y no está `AREPA_SIN_VENTANA`/`--sin-ventana`, abre el visor. Sin
  entorno gráfico **no falla**: avisa y deja la imagen en disco.
* Sin cláusula final, la gráfica solo se valida y se prepara; no escribe.

**Salida.** PNG RGB 800x480. Dos series con longitudes distintas lanzan
`ErrorGrafica`. El PNG es determinista: mismo programa, mismo archivo.

## 9. Catálogo de errores

| Clase | Cuándo |
|---|---|
| `ErrorVariable` | variable inexistente (con pista de columnas); `agregue`/`saque`/`recorra` sobre una variable no declarada |
| `ErrorColumna` | columna inexistente en `escoja/acomode/resuma/pinte/ejes/columna`; clave inexistente en un registro; `agregue` con un registro al que le falta una columna |
| `ErrorTipos` | mezcla número-texto, lógico con número, condición no lógica, conversión imposible; índice no entero; clave de registro no textual; valor no indexable; fila de `arme`/`agregue` con ancho incorrecto; destino de `agregue`/`saque`/`recorra` que no es colección |
| `ErrorOperacion` | operación sin tabla, `guarde` sobre no-tabla, potencia compleja, índice 1-based fuera de rango (lista/tabla/fila), `saque` fuera de rango |
| `ErrorGrafica` | `pinte`: tabla vacía, columna de `ejey` no numérica, histograma sin exactamente una columna, cláusula repetida, ruta de `guardela` sin `.png`, fallo al dibujar o escribir el PNG |
| `ErrorSemantico` / `ErrorEjecucion` | `devuelva`/`pare`/`siga` fuera de lugar, argumentos incorrectos, tope de ciclos, recursión profunda |
| `ErrorArchivo` / `ErrorCSV` | ruta ausente, no UTF-8, fila con exceso de campos, comillas sin cerrar |

Pruebas que los cubren: `test_expresiones.py` (tipos),
`test_estructuras.py` (índices, claves, filas incompletas, destinos no
colección, `recorra` sobre número), `test_graficas.py` (columna inexistente o
textual en `ejey`, histograma con dos columnas, ruta sin `.png`, tabla vacía,
tipo desconocido), `test_runtime.py`
(`variable_inexistente_rechazada`, `escoja_columna_inexistente`,
`suma_numero_mas_texto_rechazada`,
`operacion_sin_tabla_de_entrada_rechazada`,
`agregacion_sobre_columna_inexistente`,
`guarde_sobre_variable_no_tabla_rechazado`,
`pare/siga fuera de ciclo`, `devuelva_fuera_de_funcion_rechazado`).
