# AREPA — Arquitectura e implementaciones propias

Este documento describe cómo está organizado el proyecto, qué componentes
fueron implementados desde cero por el equipo, cómo funcionan sus
algoritmos principales y qué limitaciones tiene cada uno.

Regla del curso: toda la lógica del DSL es propia. La única herramienta
externa autorizada es ANTLR4 (el enunciado la exige para el lexer y el
parser), y solo se usa para eso.

---

## 1. Capas y módulos

```text
src/
├── lenguaje/            FRONT-END (ANTLR4 autorizado + lógica propia)
│   ├── analizador.py    orquesta lexer + parser + listener de errores
│   ├── errores.py       listener propio que traduce diagnósticos a español
│   └── arbol.py         impresión jerárquica del árbol de análisis
│
├── datos/               BIBLIOTECA PROPIA DE DATOS
│   ├── tipos.py         valores del DSL, conversiones y calendario propio
│   ├── fila.py          registro de valores
│   ├── columna.py       metadato: nombre + tipo
│   ├── lista.py         arreglo dinámico propio (índice interno 0-based)
│   ├── registro.py      pares clave→valor con callback 'al_poner'
│   ├── acceso.py        lectura/escritura 1-based sobre Lista/Registro/Tabla/Fila
│   ├── tabla.py         estructura central y sus operaciones
│   ├── lector_csv.py    máquina de estados CSV (desde cero)
│   └── escritor_csv.py  escritura CSV propia (para 'guarde')
│
├── expresiones/         BIBLIOTECA PROPIA DE EXPRESIONES
│   ├── operadores.py    aritméticos, relacionales y lógicos con tipos
│   └── evaluador.py     recorrido del árbol de ANTLR y cálculo
│
├── runtime/             BIBLIOTECA PROPIA DE EJECUCIÓN
│   ├── simbolos.py      ámbitos encadenados + funciones 'invente'
│   ├── contexto.py      estado global: símbolos, salida, tablas y errores
│   └── ejecutor.py      intérprete del programa (visitor propio)
│
├── graficas/            MOTOR GRÁFICO PROPIO (Fase 3)
│   ├── png.py           codificador PNG: chunks, CRC-32, Adler-32, DEFLATE fijo + LZ77
│   ├── fuente.py        fuente bitmap 5x7 propia
│   ├── lienzo.py        búfer RGB y primitivas rasterizadas a mano
│   ├── escalas.py       EscalaLineal, EscalaBanda y ticks "bonitos"
│   └── tipos_grafica.py Serie, Grafica y los cinco dibujos
│
├── errores_base.py      jerarquía propia de errores de todo el runtime
└── cli/main.py          interfaz de línea de comandos
```

Nota sobre variantes de organización: en lugar de un paquete `valores.py`
separado, los valores del DSL (`nada`, conversiones, tipos) viven en
`datos/tipos.py`; en lugar de un paquete `operaciones/`, las operaciones
sobre datos son métodos de `Tabla` (seleccionar, filtrar, crear columna,
conversiones) y la orquestación de asignaciones/pipeline está en
`runtime/ejecutor.py`. La matriz de trazabilidad de la sección 10 indica
exactamente dónde queda cada funcionalidad.

Dependencias entre capas (de abajo hacia arriba): `errores_base` → `datos` →
`expresiones` → `runtime` → `cli`. El motor gráfico (`graficas/`) depende solo
de `errores_base` y de la biblioteca estándar, y el ejecutor lo usa al visitar
`pinte`. Solo `lenguaje` toca el runtime de ANTLR4. Los módulos de `datos`,
`expresiones` y `graficas` no importan ninguna biblioteca externa.

---

## 2. Estructuras de datos (`datos/`)

### Tabla (`tabla.py`)

**Qué es:** el equivalente propio a un marco de datos: una lista de
`Columna` (nombre + tipo) y una lista de `Fila` (valores en el mismo
orden), con metadatos (nombre y archivo de origen).

**Cómo funcionan sus operaciones** (todas recorren filas y columnas):

* `seleccionar(nombres)`: resuelve cada nombre a su posición y construye
  filas nuevas con solo esas posiciones.
* `filtrar(predicado)`: conserva las filas donde el predicado propio
  devuelve exactamente `True`.
* `ordenar(claves)`: **merge sort propio** y estable. La comparación
  `_menor` recorre las claves en orden; el valor `nada` se considera
  mayor que cualquier otro (queda al final) y dos `nada` son iguales
  entre sí, lo que hace el ordenamiento determinista.
* `crear_columna(nombre, fn)`: agrega el valor calculado a cada fila y
  crea el metadato infiriendo el tipo.
* `quitar_duplicados()`: clave = tupla de valores de la fila; conserva
  la primera aparición.
* `rellenar_vacios(v)` / `eliminar_filas_con_vacios()`: recorridos
  lineales que respetan la semántica de `nada`.
* `agrupar(nombres)`: diccionario de claves (tuplas) conservando el
  orden de primera aparición; devuelve pares (clave, filas del grupo).
* `desde_filas(columnas, filas, …)`: constructor de clase que valida que
  cada fila traiga exactamente un valor por columna (lo usa `arme`).
* `fila_como_registro(indice)`: devuelve la fila como `Registro` enlazado;
  cada `poner()` del registro llama a `poner_celda`.
* `poner_celda(indice, columna, valor)`: actualiza una celda y re-infiera
  el tipo de la columna.
* `poner_fila(indice, valores)`: reemplaza una fila completa (lista,
  tupla o `Fila`) y re-infiera todos los tipos.

**Limitaciones:** las operaciones copian filas (no hay vistas perezosas
ni índices); el costo es O(n) o O(n log n) según la operación. La copia de
una tabla es superficial en los valores atómicos y nueva en filas/columnas.

### Lista, Registro y acceso (`lista.py`, `registro.py`, `acceso.py`)

**`Lista`** es un arreglo dinámico propio: guarda elementos en orden y
expone `largo`, `obtener`, `poner`, `agregar`, `quitar` y `copiar`. Su
índice interno es 0-based; el runtime traduce desde la semántica 1-based
del lenguaje (D12). `quitar` devuelve el elemento eliminado y los errores
de rango son `ErrorEjecucion` con el largo actual.

**`Registro`** guarda pares clave→valor en orden de primera aparición con
dos listas paralelas y búsqueda lineal (sin `dict` ni
`collections.OrderedDict`). `obtener` lanza `ErrorColumna` con las claves
disponibles; `poner` actualiza sin mover de posición y avisa por el
callback opcional `al_poner`. Ese callback es lo que permite que una fila
de tabla enlazada escriba de vuelta en la tabla.

**`acceso`** centraliza la semántica de índices para el evaluador y el
ejecutor:

* `obtener(contenedor, indice)`: lista/fila por entero 1..N; tabla por
  entero 1..N (devuelve `Registro` enlazado); registro por clave de texto;
* `asignar(contenedor, indice, valor)`: actualiza lista, registro, fila o
  una fila completa de tabla (normaliza con `valores_para_fila`);
* `valores_para_fila(tabla, valor)`: acepta una `Lista`/`Fila` (por
  posición) o un `Registro` (por nombre de columna) y valida que no falte
  ninguna columna ni sobre ningún valor.

Los índices fuera de rango producen `ErrorOperacion` con numeración
1-based; una clave inexistente, `ErrorColumna`; un tipo no indexable o una
clave no textual, `ErrorTipos`.

### Tipos (`tipos.py`)

**Qué hace:** clasifica valores (`numero`, `texto`, `logico`, `nada`),
convierte campos crudos del CSV al valor más ajustado (entero → decimal
→ lógico → texto), convierte valores al tipo declarado por `convierta`
y valida fechas.

**Cómo lo hace:** sin bibliotecas. La conversión usa intentos sucesivos
de parseo propio; la validación de fechas AAAA-MM-DD implementa el
calendario gregoriano completo (meses de 28-31 días y año bisiesto con
la regla de los 100/400).

**Limitaciones:** las fechas se guardan como texto validado (no hay
aritmética de fechas); los decimales usan la aritmética binaria de
Python; `convierta` solo acepta el formato AAAA-MM-DD.

---

## 3. Lector CSV propio (`lector_csv.py`)

**Qué hace:** lee archivos (o texto en memoria, para las pruebas) y
produce una `Tabla` propia. Reemplaza a `csv.DictReader` y
`pandas.read_csv`.

**Cómo funciona:** una máquina de estados que recorre la línea carácter
a carácter con dos estados:

1. **FUERA**: una comilla al inicio de campo activa el modo DENTRO; el
   separador corta el campo; cualquier otro carácter se acumula.
2. **DENTRO**: una comilla seguida de otra es una comilla literal
   (escape `""`); una comilla sola vuelve a FUERA; el separador dentro
   de comillas NO corta el campo.

Además: las líneas vacías se descartan (conservando su número para los
errores); los campos faltantes se rellenan con `nada`; una fila con más
campos que el encabezado o con comillas sin cerrar lanza `ErrorCSV` con
el número de línea del archivo.

**Limitaciones:** no soporta campos con comillas "en medio" sin abrir
campo (regla: las comillas solo son especiales al inicio del campo); no
detecta el separador automáticamente (lo da `monte ... separador "..."`).

---

## 4. Motor de expresiones (`expresiones/`)

### Operadores (`operadores.py`)

**Qué hace:** cada operador del DSL es una función propia que valida
tipos con el sistema propio y decide qué hacer con `nada`.

**Reglas semánticas del equipo:**

* `nada` se propaga: `nada + 1`, `nada == 5`, `obvio y nada` producen
  `nada` (estilo SQL);
* comparar número con texto lanza `ErrorTipos` (sin coerción silenciosa);
* dividir entre cero no es error: `1/0` produce `infinito`, `-1/0`
  produce `-infinito` y `0/0` produce `nada` (indefinido);
* el módulo entre cero no es error: produce `nada` (indefinido);
* la potencia que desborda produce `infinito` (con su signo); solo sigue
  siendo error el resultado complejo (p. ej. `(-1) ^ 0.5`);
* los lógicos exigen `obvio`/`falso`.

### Evaluador (`evaluador.py`)

**Qué hace:** recorre el árbol de análisis que produce ANTLR4 y calcula
el valor de cada expresión. No usa `eval()` ni `exec()`: la precedencia
(`o < y < no < comparación < +- < */% < - unario < ^ < acceso`) ya quedó
codificada en la forma del árbol por la gramática; el evaluador solo la
recorre de abajo hacia arriba.

**Literales y acceso:** `visitLista_literal`, `visitRegistro_literal` y
`visitTabla_literal` construyen `Lista`, `Registro` y `Tabla`;
`visitAcceso` aplica `datos/acceso.obtener` una vez por cada índice
encadenado, de modo que `gente[1]["edad"]` funciona sin casos especiales.

**Callback `evaluar_expresion`:** una expresión general puede ser un
pipeline completo. En vez de duplicar esa lógica en el evaluador, este
recibe del ejecutor el callback `evaluar_expresion` y delega en él los
nodos `expresion`; así `cuenteme t |> escoja [a]` y los literales que
contienen etapas se evalúan con el mismo motor.

**Modos:** `modo_columna` devuelve el nombre sin resolverlo (lo usan las
agregaciones de `resuma`); `modo_resuma` lo activa el ejecutor solo
mientras evalúa los ítems de `resuma`. Fuera de `resuma`, una agregación
evalúa su primer argumento como valor (tabla o lista) y los demás como
nombre de columna o texto; `columna(tabla, nombre)` también recibe el
segundo argumento como nombre.

**Resolución de nombres:** si hay fila en contexto y el nombre es
columna, devuelve la celda; si no, busca la variable en la tabla de
símbolos; si tampoco existe, `ErrorVariable` lista las columnas
disponibles como pista. En modo columna (agregaciones) el nombre se
devuelve tal cual, porque `sume(precio)` recibe un nombre, no un valor.

**Limitaciones:** la línea/columna de un error de tipos es la del inicio
de la expresión (aproximación); no hay coerción número↔texto.

---

## 5. Tabla de símbolos y contexto (`runtime/`)

### `TablaSimbolos` (`simbolos.py`)

**Qué hace:** ámbitos encadenados (hijo → padre). `declarar` escribe en
el ámbito actual; `buscar` y `asignar` suben por la cadena;
`existe` consulta sin fallar. Los nombres se validan con la regla propia
del DSL (letra/ñ/tilde o `_` al inicio). Las funciones `invente` se
guardan como `FuncionArepa` con su nodo de cuerpo y el ámbito donde se
definieron (closure), lo que permite recursión.

**Decisión:** `x = valor` declara si el nombre no existe en ningún
ámbito visible y asigna si existe (semántica tipo Python, documentada).
Los bloques de `fijese_si` no crean ámbito; solo las funciones.

### `ContextoEjecucion` (`contexto.py`)

**Qué hace:** guarda los símbolos raíz, la salida del programa y el
registro de errores ocurridos durante la corrida. El formato de valores
y tablas en texto es propio (ancho calculado por columna, `nada`
visible, recorte de filas), reemplazando a `tabulate`.

---

## 6. Ejecutor del DSL (`runtime/ejecutor.py`)

**Qué hace:** interpreta el programa recorriendo el árbol de ANTLR4 con
un visitor propio.

**Puntos clave:**

* **Pipeline**: la primera etapa carga (`monte`) o evalúa un valor; cada
  etapa `|>` siguiente debe ser una operación de datos que recibe la
  tabla anterior y produce una nueva (decisión D3: la tabla de entrada
  nunca se modifica).
* **Agregaciones**: `junte por [...]` guarda las claves de agrupación;
  `resuma` agrupa con `Tabla.agrupar` y calcula por grupo: `cuente`,
  `sume`, `promedie`, `mediana` (orden por inserción propio), `minimo`,
  `maximo` (búsqueda lineal propia) y `desviacion` (estándar
  poblacional: raíz de la media de las diferencias al cuadrado). Los
  `nada` se ignoran en el cálculo; si el grupo queda vacío, el resultado
  es `nada`. Fuera de `resuma`, `_agregacion_fuera_de_resuma` acepta
  `sume(tabla, columna)`, `sume(lista)`, `cuente(tabla)`,
  `cuente(tabla, columna)` y las demás formas equivalentes.
* **Estructuras propias**: `visitInstruccion_agregue`,
  `visitInstruccion_saque` y `visitCiclo_recorra` mutan o recorren
  `Lista`/`Tabla`; `visitAsignacion` detecta índices encadenados y llama a
  `datos/acceso.asignar`. `visitTabla_literal` construye con
  `Tabla.desde_filas`. El recorrido de tabla toma una instantánea de las
  filas y entrega un `Registro` enlazado por vuelta; el de lista copia
  los elementos.
* **Funciones incorporadas**: `_invocar` despacha `largo`, `columna` y
  `columnas` antes de buscar funciones `invente`; `largo` acepta tabla,
  lista, registro o texto; `columna` devuelve una `Lista` de valores y
  `columnas` una `Lista` de nombres.
* **Funciones**: `invente` registra la función; al llamarla se crea un
  ámbito hijo con los parámetros enlazados; `devuelva` interrumpe el
  cuerpo con `RetornoFuncion` (control de flujo interno, no un error);
  fuera de una función es error semántico. La recursión que agota la
  pila no muestra `RecursionError`: produce `ErrorEjecucion` en español
  que pide revisar el caso base.
* **Condicionales**: `fijese_si` exige condición lógica (`nada` es
  error); `sino` encadena con otro `fijese_si` o un bloque.
* **Ciclos**: `mientras` reevalúa la condición (lógica, `nada` es error)
  en cada vuelta; `repita N veces` evalúa el conteo una vez (entero ≥
  0); `repita i desde A hasta B (paso P)` cuenta con `i` inclusive
  (paso 1/-1 por defecto, 0 prohibido). `pare`/`siga` viajan como
  señales internas (`SalirCiclo`/`SeguirCiclo`, como `RetornoFuncion`);
  fuera de un ciclo son error semántico. Tope de 1 000 000 de vueltas
  con mensaje en español en vez de colgarse.
* **`pinte`**: valida que la tabla exista y no esté vacía y que las columnas
  de `ejex`/`ejey` existan y sean numéricas donde corresponde; aplica los
  valores por defecto de las columnas y delega el dibujo en el motor gráfico
  (`graficas/`), y el cierre en `guardela` (PNG en la ruta) o `muestrela`
  (`salidas/<tabla>_<tipo>.png`). Ver `docs/11_informe_fase3.md` §5.
* **`monte`/`guarde`**: usan el lector y escritor CSV propios; los
  errores de archivo y de formato incluyen la ruta y la línea.

### 6.1 Flujo de una tabla en memoria

El mismo camino se puede seguir sin CSV, con una tabla construida por
`arme`:

```text
gastos = arme [mes, categoria, valor] con [["Enero", "Mercado", 120000], …]
        │
        ├─ literal: el evaluador construye filas y llama a Tabla.desde_filas
        ├─ acceso: gastos[1] → Registro enlazado; gastos[1]["valor"] → celda
        ├─ recorrido: recorra fila en gastos { … fila["valor"] … }
        ├─ agregación: sume(gastos, valor) / cuente(gastos) / largo(gastos)
        ├─ pipeline: gastos |> junte por [categoria] |> resuma …
        └─ guarde resumen como "salidas/memoria_resumen.csv"
```

Cada paso usa las estructuras propias: `Tabla.desde_filas` valida el
ancho de las filas; `acceso.obtener` traduce el índice 1-based y devuelve
un `Registro` cuyo `al_poner` escribe en la tabla; `_calcular_sobre_valores`
ignora los `nada`; `EscritorCSV` produce el archivo UTF-8. El programa
completo es `ejemplos/memoria.arepa` y su salida versionada es
`salidas/memoria_resumen.csv`.

### 6.2 Motor gráfico propio (`graficas/`)

**Qué hace:** convierte una tabla en un PNG RGB 800x480 sin bibliotecas
externas. Reemplaza a matplotlib para los cinco tipos del DSL.

**Cómo funciona**, de abajo hacia arriba:

* `png.py` arma la firma y los chunks `IHDR`/`IDAT`/`IEND` con **CRC-32**
  propio (tabla precalculada), comprime con **LZ77 + Huffman fijo**
  (BTYPE=01, `_comprimir_fijo`) o **bloques guardados** (BTYPE=00,
  `_comprimir_guardado`), envuelve el flujo con la cabecera y la **suma
  Adler-32** de zlib, y antepone el filtro 0 a cada fila.
* `lienzo.py` es el `bytearray` RGB con las primitivas: `poner`, `linea`
  (Bresenham con grosor por sello cuadrado), `rectangulo(_relleno)`,
  `circulo_relleno` (por filas con `math.isqrt`) y `texto`. Todo trazo se
  recorta contra los bordes.
* `fuente.py` define los glifos 5x7 del ASCII imprimible y normaliza el
  texto con NFD (quita tildes), con un mapa propio para los signos que no se
  descomponen.
* `escalas.py` traduce dominio a píxeles con `EscalaLineal` y
  `EscalaBanda`, genera ticks con pasos "bonitos" (`paso_bonito`) y formatea
  las etiquetas (`formatear`).
* `tipos_grafica.py` comparte el marco (título, ejes, rejilla, leyenda) y
  dibuja los cinco tipos; expone `cuartiles` y `cubetas_histograma` como
  funciones públicas para poder probar la estadística sin mirar píxeles.

**Integración:** `EjecutorArepa.visitInstruccion_grafica`
(`runtime/ejecutor.py:502`) resuelve las cláusulas, aplica los valores por
defecto, arma una `Serie` por columna de `ejey`, llama a
`dibujar(tipo, series, ancho=800, alto=480)` y escribe el PNG. Los fallos
se lanzan como `ErrorGrafica` con línea y columna.

**Limitaciones:** un solo tamaño de figura (800x480), filtro PNG 0,
profundidad 8 y color RGB; sin antialiasing; sin filtros 1-4, sin Huffman
dinámico, sin escalas logarítmicas ni de fechas. El detalle está en
`docs/11_informe_fase3.md` §3 y §4.

---

## 7. Diagnóstico (`errores_base.py` + `lenguaje/errores.py`)

* **Léxicos y sintácticos**: el listener propio captura los mensajes de
  ANTLR sin detener el análisis y los traduce a español: nombres de
  tokens traducidos (`NL` → "un salto de línea"), conjuntos esperados
  limitados a 6 opciones, sin saltos crudos y con pista cuando se usa
  una palabra reservada como variable.
* **Semánticos y de ejecución**: jerarquía propia (`ErrorSemantico`,
  `ErrorVariable`, `ErrorColumna`, `ErrorTipos`, `ErrorOperacion`,
  `ErrorEjecucion`, `ErrorArchivo`, `ErrorCSV`) con mensaje comprensible,
  línea y columna del programa cuando se conocen, y contexto (por
  ejemplo, la línea del CSV que falló).

**Limitación:** en errores descubiertos sobre datos (por ejemplo, una
celda que no convierte), la línea del programa es aproximada; la línea
del dato sí es exacta.

---

## 8. Pruebas

`python3 pruebas/test_proyecto.py` ejecuta las ocho suites:

| Suite | Archivo | Pruebas |
|---|---|---|
| Front-end (léxico y sintáctico) | `test_front.py` | 55 |
| Estructura del árbol de análisis | `test_arbol.py` | 28 |
| Biblioteca propia de datos | `test_datos.py` | 43 |
| Estructuras propias (listas, registros, tablas) | `test_estructuras.py` | 48 |
| Evaluador de expresiones propio | `test_expresiones.py` | 16 |
| Tabla de símbolos y contexto propios | `test_simbolos.py` | 15 |
| Runtime propio (programas completos) | `test_runtime.py` | 51 |
| Motor gráfico y visualización propia | `test_graficas.py` | 63 |

Total: **319 pruebas** (fuente única verificable con
`python3 herramientas/chequeo_pruebas.py`, que falla si algún total
cambia). Las 55 de front-end desglosan en: 10 programas
positivos, 22 negativos, 10 de diagnóstico (línea/columna exactas,
robustez, comentarios, números incompletos y ausencia de duplicados) y 13
de CLI. Las 28 de árbol verifican la estructura jerárquica y la
precedencia recorriendo el árbol programáticamente. Las 48 de estructuras
cubren listas, registros, `arme`, acceso 1-based, asignación indexada,
`agregue`/`saque`, `recorra`, agregaciones en memoria, builtins y las
regresiones `cuenteme t |> escoja [a]` y `-2 ^ 2 = -4`. Las 51 de runtime
incluyen 19 de ciclos (`mientras`, `repita`, `pare`/`siga`) y 1 de
columnas con nombre reservado (D5). Las 63 de gráficas cubren el
codificador PNG (20), la fuente (3), el lienzo (7), las escalas (4), los
cinco dibujos y regresiones de ejes (14), la integración con el runtime (11)
y el caso de estudio (4). Ninguna prueba usa bibliotecas externas para el
trabajo que se prueba.

### Matriz de cobertura del primer corte

| Requisito del corte | Evidencia positiva | Evidencia negativa | Resultado |
|---|---|---|---|
| Programa mínimo (`quihubo`/`chao`) | `test_arbol.py::arbol_programa_minimo` | `n01_falta_chao`, `n14_chao_incorrecto` | OK |
| Asignaciones | `01_asignaciones_expresiones.arepa` | `n06_asignacion_incompleta` | OK |
| Expresiones aritméticas y booleanas | `01` + `08_casos_borde.arepa` | `n08_operador_colgante` | OK |
| Comparaciones sencillas | `03_seleccion_filtro.arepa` | `test_expresiones.py::comparacion_numero_con_texto_rechazada` | OK |
| Precedencia y asociatividad | `test_arbol.py` (11 casos de precedencia y asociatividad) | `n08` | OK |
| Carga de CSV (`monte`) | `02_carga_y_guardado.arepa` | `test_runtime.py::monte_con_archivo_inexistente` | OK |
| Selección de columnas | `03` + `test_arbol.py::arbol_de_seleccion` | `n04_corchete_sin_cerrar` | OK |
| Filtros (`deje donde`) | `03` + `test_arbol.py::arbol_de_filtro` | `n05_deje_sin_donde` | OK |
| Visualización (tipo de gráfica y columnas) | `05_graficas.arepa` + `test_arbol.py::arbol_de_visualizacion` | `n09_pinte_tipo_invalido`, `n13_pinte_sin_tabla` | OK (genera PNG desde el Corte 3) |
| Árbol de análisis | `test_arbol.py` (28 casos) + CLI `--arbol` | — (siempre generable) | OK |
| Errores con línea y columna | `test_front.py` sección diagnóstico (10) | los 22 negativos validan posición | OK |
| Tokens (`--tokens`) | `test_front.py` CLI | — | OK |
| Comentarios | `08_casos_borde.arepa` (entre sentencias) | — (siempre válidos) | OK |
| Identificadores (tildes, ñ) | `08_casos_borde.arepa` | `n10_identificador_invalido` | OK |
| Colisiones reservada/ID/columna | `08_casos_borde.arepa` (`numerito`, `y2`) | `n11_reservada_como_variable` | OK |
| Cadenas y escapes | `08_casos_borde.arepa` | `n02_cadena_sin_cerrar` | OK |
| Números (enteros/decimales) | `01` (`15000.5`) | `test_expresiones.py` (`.5` y `3.` fallan) | OK |
| Booleanos (`obvio`/`falso`) | `01` | `test_expresiones.py::logico_con_numero_rechazado` | OK |
| Condicionales y funciones (sintaxis) | `06_funciones_condicional.arepa` | `n07_fijese_sin_parentesis` | OK |
| CLI (códigos 0/1/2, `--arbol`, `--tokens`) | `test_front.py` CLI (13) | código 1 y 2 verificados | OK |

### Matriz de cobertura de estructuras propias

| Requisito | Evidencia positiva | Evidencia negativa | Resultado |
|---|---|---|---|
| Listas propias y literales | `test_estructuras.py::lista_literal_y_acceso_uno_based`, `::lista_vacia_tiene_largo_cero`, `10_estructuras.arepa` | `::lista_indice_fuera_de_rango`, `::lista_indice_de_texto_rechazado` | OK |
| Registros propios y literales | `::registro_literal_con_claves_id`, `::registro_con_claves_de_cadena`, `::registro_conserva_orden_de_claves` | `::registro_clave_inexistente`, `n22_registro_sin_dos_puntos` | OK |
| Tablas en memoria (`arme`) | `::arme_con_filas`, `::arme_sin_filas`, `::tabla_desde_filas_directa` | `::arme_fila_con_largo_incorrecto`, `n21_fila_incompleta` | OK |
| Acceso 1-based encadenado | `::lista_anidada_acceso_encadenado`, `::acceso_directo_sobre_lista_literal` | `::acceso_a_tabla_fuera_de_rango_menciona_filas` | OK |
| Asignación indexada | `::asignacion_a_lista`, `::asignacion_a_registro`, `::asignacion_a_celda_de_tabla`, `::asignacion_a_fila_completa_con_lista`, `::asignacion_a_fila_completa_con_registro` | `::asignacion_indexada_variable_inexistente` | OK |
| `agregue` / `saque` | `::agregue_a_lista`, `::agregue_a_tabla_con_lista`, `::agregue_a_tabla_con_registro`, `::saque_de_lista`, `::saque_de_tabla` | `::agregue_a_destino_no_coleccion`, `::agregue_fila_con_largo_incorrecto`, `::saque_posicion_invalida` | OK |
| `recorra` (snapshot, `pare`/`siga`) | `::recorra_lista_acumula`, `::recorra_tabla_lee_columnas`, `::recorra_tabla_muta_celdas`, `::recorra_con_pare`, `::recorra_con_siga` | `::recorra_sobre_numero_rechazado` | OK |
| Agregaciones en memoria | `::agregaciones_de_tabla`, `::agregaciones_de_lista`, `::mediana_par_e_impar`, `::desviacion_poblacional`, `::cuente_tabla_y_columna_con_nada` | `test_runtime.py::agregacion_sobre_columna_inexistente` | OK |
| Builtins `largo`/`columna`/`columnas` | `::largo_de_tabla_lista_registro_y_texto`, `::columna_devuelve_lista`, `::columnas_devuelve_nombres` | — (aridad/tipo cubiertos en runtime) | OK |
| Regresión pipeline en `cuenteme` | `::cuenteme_pipeline_imprime_la_tabla` | — | OK |
| Regresión `-2 ^ 2 = -4` | `::potencias_precedencia_y_signo`, `test_arbol.py::potencia_antes_que_menos_unario` | `test_expresiones.py::potencia_casos_borde` | OK |

---

## 9. Dependencias

| Nombre | Versión | Uso | Por qué está permitida | Qué reemplazaría si se eliminara |
|---|---|---|---|---|
| `antlr4-python3-runtime` | 4.13.2 | ejecutar el lexer/parser generados desde `Arepa.g4` | ANTLR4 la especifica el enunciado del curso | todo el reconocimiento léxico y sintáctico |

No hay más dependencias. En particular: no hay pandas, NumPy,
Matplotlib, Polars, tabulate, openpyxl ni equivalentes, ni en el código
ni en las fases siguientes. Las estructuras propias
(`Lista`, `Registro`, `Tabla`), los builtins y el motor gráfico de la
Fase 3 se implementaron con el lenguaje anfitrión y no agregaron ninguna
dependencia externa.

---

## 10. Matriz de trazabilidad

Para la sustentación: cada funcionalidad exigida y dónde está
implementada, con su prueba asociada.

| Funcionalidad | Módulo (archivo) | Función / clase | Prueba |
|---|---|---|---|
| Nombres de columnas | `datos/tabla.py` | `Tabla.nombres_columnas` | `test_datos.py::csv_archivo_real_del_proyecto` |
| Filas (registros) | `datos/fila.py` | clase `Fila` | `test_datos.py::csv_valido_basico` |
| Columnas (metadato) | `datos/columna.py` | clase `Columna` | `test_datos.py::tabla_conversion_de_columna` |
| Acceso por columna | `datos/tabla.py` | `Tabla.valores_columna` | `test_datos.py::tabla_ordenamiento_propio_ascendente` |
| Acceso por fila | `datos/tabla.py` | `Tabla.filas` + `Fila.valor_en` | `test_datos.py::tabla_insertar_fila_al_final_y_en_posicion` |
| Cantidad de registros | `datos/tabla.py` | `Tabla.num_filas` | `test_datos.py::tabla_cuenta_filas_y_columnas` |
| Cantidad de columnas | `datos/tabla.py` | `Tabla.num_columnas` | `test_datos.py::tabla_cuenta_filas_y_columnas` |
| Selección de columnas | `datos/tabla.py` | `Tabla.seleccionar` | `test_datos.py::tabla_seleccion_de_columnas` |
| Filtrado | `datos/tabla.py` | `Tabla.filtrar` | `test_datos.py::tabla_filtrado` + `test_runtime.py::deje_donde_filtra_filas` |
| Inserción de fila | `datos/tabla.py` | `Tabla.insertar_fila` | `test_datos.py::tabla_insertar_fila_al_final_y_en_posicion` |
| Eliminación de fila | `datos/tabla.py` | `Tabla.eliminar_fila` | `test_datos.py::tabla_eliminar_fila_por_posicion` |
| Inserción de columna | `datos/tabla.py` | `Tabla.insertar_columna` / `Tabla.crear_columna` | `test_datos.py::tabla_insertar_columna_con_valores` |
| Eliminación de columna | `datos/tabla.py` | `Tabla.eliminar_columna` | `test_datos.py::tabla_eliminar_columna` |
| Copia | `datos/tabla.py` | `Tabla.copiar` | `test_runtime.py::pipeline_completo_con_cree` |
| Representación legible | `datos/tabla.py` | `Tabla.texto_tabla` | `test_datos.py::tabla_texto_formato_propio` |
| Ordenamiento propio | `datos/tabla.py` | `Tabla.ordenar` (merge sort) | `test_datos.py::tabla_ordenamiento_estable_por_dos_claves` |
| Duplicados y vacíos | `datos/tabla.py` | `quitar_duplicados`, `rellenar_vacios`, `eliminar_filas_con_vacios` | `test_datos.py::tabla_quitar_duplicados_conserva_primera` |
| Agrupamiento | `datos/tabla.py` | `Tabla.agrupar` | `test_datos.py::tabla_agrupar_propio` |
| Lector CSV propio | `datos/lector_csv.py` | `LectorCSV._partir_campos` (máquina de estados) | `test_datos.py` (12 casos csv_*) |
| Escritor CSV propio | `datos/escritor_csv.py` | `EscritorCSV.escribir` | `test_datos.py::escritor_csv_roundtrip` |
| Tipos y valores (`nada`) | `datos/tipos.py` | `NADA`, `texto_a_valor`, `convertir_a_tipo` | `test_datos.py::tipos_*` |
| Fechas sin bibliotecas | `datos/tipos.py` | `_es_fecha_valida` (calendario propio) | `test_datos.py::tipos_fecha_valida_propia` |
| Enteros/decimales/cadenas/booleanos | `expresiones/evaluador.py` | `visitAtomo`, `visitCadena` | `test_expresiones.py::aritmetica_basica` |
| Suma, resta, mult., div., módulo, potencia | `expresiones/operadores.py` | `sumar`…`potenciar` | `test_expresiones.py::precedencia_multiplicacion_sobre_suma` |
| Comparaciones | `expresiones/operadores.py` | `igual`…`mayor_igual` | `test_expresiones.py::comparaciones_numericas` |
| AND / OR / NOT | `expresiones/operadores.py` | `conjuncion`, `disyuncion`, `negar_logico` | `test_expresiones.py::logicos_y_o_no` |
| Paréntesis y precedencia | gramática (`Arepa.g4`) + `evaluador.py` | jerarquía de reglas | `test_expresiones.py::parentesis_anidados` |
| Valores nulos en expresiones | `expresiones/operadores.py` | propagación de `NADA` | `test_expresiones.py::nada_se_propaga` |
| Identificadores (columna/variable) | `expresiones/evaluador.py` | `_resolver_nombre` | `test_runtime.py::variable_inexistente_rechazada` |
| Errores de tipos | `expresiones/operadores.py` | `ErrorTipos` con mensaje claro | `test_expresiones.py::suma_numero_mas_texto_rechazada` |
| Tabla de símbolos: declarar/consultar | `runtime/simbolos.py` | `TablaSimbolos.declarar`/`buscar` | `test_simbolos.py::declarar_y_consultar` |
| Tabla de símbolos: actualizar | `runtime/simbolos.py` | `TablaSimbolos.asignar` | `test_simbolos.py::actualizar_valor_existente` |
| Símbolos no declarados | `runtime/simbolos.py` | `ErrorVariable` en `buscar`/`asignar` | `test_simbolos.py::consultar_inexistente_rechazado` |
| Ámbitos (padre/hijo, sombra) | `runtime/simbolos.py` | `hijo`, `existe_local` | `test_simbolos.py::sombra_local_sobre_el_padre` |
| Validación de identificadores | `runtime/simbolos.py` | `validar_identificador` | `test_simbolos.py::identificador_invalido_rechazado` |
| Funciones `invente` (closures) | `runtime/simbolos.py` + `runtime/ejecutor.py` | `FuncionArepa`, `_llamar_funcion` | `test_runtime.py::invente_devuelva_y_recursion` |
| Contexto de ejecución | `runtime/contexto.py` | `ContextoEjecucion` | `test_simbolos.py::contexto_reune_simbolos_salida_y_tablas` |
| Registro de errores en contexto | `runtime/contexto.py` | `registrar_error` | `test_simbolos.py::contexto_registra_errores` |
| Asignaciones | `runtime/ejecutor.py` | `visitAsignacion` | `test_runtime.py::asignaciones_y_reasignacion` |
| Creación de columnas calculadas | `runtime/ejecutor.py` | `_aplicar_operacion` (CREE) | `test_runtime.py::pipeline_completo_con_cree` |
| Conversiones básicas | `runtime/ejecutor.py` | `_aplicar_operacion` (CONVIERTA) | `test_runtime.py::convierta_tipo_de_columna` |
| Carga CSV (`monte`) | `runtime/ejecutor.py` | `_cargar` → `LectorCSV` | `test_runtime.py::monte_carga_csv_real` |
| Agrupamiento y agregaciones propias | `runtime/ejecutor.py` | `_ejecutar_resuma`, `_calcular_agregacion` | `test_runtime.py::junte_resuma_agregaciones` |
| Guardado (`guarde`) | `runtime/ejecutor.py` | `visitInstruccion_guarde` → `EscritorCSV` | `test_runtime.py::guarde_escribe_csv_legible` |
| Visualización (`pinte`) | `runtime/ejecutor.py` | `visitInstruccion_grafica` | `test_graficas.py::runtime_los_cinco_tipos_generan_png_valido`, `test_runtime.py::pinte_valida_columnas_de_la_grafica` |
| Codificador PNG propio | `graficas/png.py` | `codificar_png`, `crc32`, `adler32`, `_comprimir_fijo`, `_BuscadorLz77` | `test_graficas.py::firma_ihdr_idat_iend_en_orden`, `::crc32_vector_conocido_y_comparacion_independiente`, `::adler32_vector_conocido`, `::roundtrip_fijo_conserva_las_scanlines` |
| Lienzo RGB propio | `graficas/lienzo.py` | `Lienzo` (`poner`, `linea`, `rectangulo_relleno`, `circulo_relleno`, `texto`) | `test_graficas.py::lienzo_*` (7 casos) |
| Fuente bitmap 5x7 | `graficas/fuente.py` | `GLIFOS`, `normalizar_texto`, `filas` | `test_graficas.py::fuente_*` (3 casos) |
| Escalas de ejes | `graficas/escalas.py` | `EscalaLineal`, `EscalaBanda`, `paso_bonito`, `formatear` | `test_graficas.py::escalas_*` (4 casos) |
| Los cinco tipos de gráfica | `graficas/tipos_grafica.py` | `dibujar`, `Grafica`, `_dibujar_barras`…`_dibujar_cajas` | `test_graficas.py::barras_genera_png_valido`, `::lineas_*`, `::histograma_*`, `::dispersion_*`, `::cajas_*` |
| Estadística de cajas e histograma | `graficas/tipos_grafica.py` | `cuartiles`, `cubetas_histograma` | `test_graficas.py::cajas_cuartiles_con_datos_conocidos`, `::histograma_usa_las_cubetas_esperadas` |
| Caso de estudio reproducible | `caso_estudio/programa.arepa` | flujo completo (carga → resumen → 5 gráficas) | `test_graficas.py::caso_estudio_*` (4 casos) |
| Diagnóstico léxico/sintáctico | `lenguaje/errores.py` | `ErroresArepa`, `_traducir` | `test_front.py` (22 negativas) |
| Árbol de análisis | `lenguaje/arbol.py` | `imprimir_arbol` | `test_front.py` (CLI `--arbol`) |
| Errores semánticos y de ejecución | `errores_base.py` | jerarquía `ErrorArepa` | `test_simbolos.py::contexto_registra_errores` |
| Integración DSL → árbol → biblioteca propia | `runtime/ejecutor.py` | flujo completo | `test_runtime.py` (51 casos) |
| Ciclos `mientras`/`repita` | `runtime/ejecutor.py` | `visitCiclo_mientras`, `visitCiclo_repita`, `visitInstruccion_pare/siga` | `test_runtime.py` (19 casos de ciclos) + `09_ciclos.arepa`, `n18`, `n19`, `n20` |
| Lista propia | `datos/lista.py` | `Lista` (`largo`, `obtener`, `poner`, `agregar`, `quitar`) | `test_estructuras.py` (5 casos de lista) |
| Registro propio | `datos/registro.py` | `Registro` (`obtener`, `poner`, `claves`, `al_poner`) | `test_estructuras.py` (5 casos de registro) |
| Acceso 1-based | `datos/acceso.py` | `obtener`, `asignar`, `valores_para_fila` | `test_estructuras.py` (acceso y asignación indexada) |
| Tabla desde filas / celdas | `datos/tabla.py` | `desde_filas`, `fila_como_registro`, `poner_celda`, `poner_fila` | `test_estructuras.py::arme_*`, `::asignacion_*` |
| Literales de estructuras | `expresiones/evaluador.py` | `visitLista_literal`, `visitRegistro_literal`, `visitTabla_literal` | `test_estructuras.py`, `test_arbol.py::arbol_de_tabla_literal` |
| `agregue` / `saque` | `runtime/ejecutor.py` | `visitInstruccion_agregue`, `visitInstruccion_saque` | `test_estructuras.py` (8 casos) |
| `recorra` | `runtime/ejecutor.py` | `visitCiclo_recorra` | `test_estructuras.py` (6 casos) + `10_estructuras.arepa` |
| Agregaciones fuera de `resuma` | `runtime/ejecutor.py` | `_agregacion_fuera_de_resuma`, `_calcular_sobre_valores` | `test_estructuras.py::agregaciones_*` |
| Builtins `largo`/`columna`/`columnas` | `runtime/ejecutor.py` | `_largo`, `_columna`, `_columnas` | `test_estructuras.py::largo_*`, `::columna_*`, `::columnas_*` |
| Callback `evaluar_expresion` | `expresiones/evaluador.py` + `runtime/ejecutor.py` | `visitExpresion` delegado | `test_estructuras.py::cuenteme_pipeline_imprime_la_tabla` |
| Precedencia `-2 ^ 2 = -4` | gramática + `expresiones/evaluador.py` | `potencia` → `acceso` → `atomo` | `test_estructuras.py::potencias_precedencia_y_signo`, `test_arbol.py::potencia_antes_que_menos_unario` |
