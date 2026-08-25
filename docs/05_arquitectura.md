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
│   ├── tipos.py         valores, conversiones y calendario propio
│   ├── fila.py          registro de valores
│   ├── columna.py       metadato: nombre + tipo
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
│   ├── contexto.py      estado global y salida formateada
│   └── ejecutor.py      intérprete del programa (visitor propio)
│
├── errores_base.py      jerarquía propia de errores de todo el runtime
└── cli/main.py          interfaz de línea de comandos
```

Dependencias entre capas (de abajo hacia arriba): `errores_base` →
`datos` → `expresiones` → `runtime` → `cli`. Solo `lenguaje` toca el
runtime de ANTLR4. Los módulos de `datos` y `expresiones` no importan
ninguna biblioteca externa.

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

**Limitaciones:** las operaciones copian filas (no hay vistas perezosas
ni índices); el costo es O(n) o O(n log n) según la operación.

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
* dividir o sacar módulo entre cero lanza `ErrorOperacion`;
* los lógicos exigen `obvio`/`falso`.

### Evaluador (`evaluador.py`)

**Qué hace:** recorre el árbol de análisis que produce ANTLR4 y calcula
el valor de cada expresión. No usa `eval()` ni `exec()`: la precedencia
(`o < y < no < comparación < +- < */% < ^ derecha < - unario`) ya quedó
codificada en la forma del árbol por la gramática; el evaluador solo la
recorre de abajo hacia arriba.

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

**Qué hace:** guarda los símbolos raíz y la salida del programa. El
formato de valores y tablas en texto es propio (ancho calculado por
columna, `nada` visible, recorte de filas), reemplazando a `tabulate`.

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
  es `nada`.
* **Funciones**: `invente` registra la función; al llamarla se crea un
  ámbito hijo con los parámetros enlazados; `devuelva` interrumpe el
  cuerpo con `RetornoFuncion` (control de flujo interno, no un error);
  fuera de una función es error semántico.
* **Condicionales**: `fijese_si` exige condición lógica (`nada` es
  error); `sino` encadena con otro `fijese_si` o un bloque.
* **`pinte`**: valida que la tabla exista y que las columnas de
  `ejex`/`ejey` existan (valor semántico real en Fase 1) y avisa que la
  imagen llega en la Fase 3.
* **`monte`/`guarde`**: usan el lector y escritor CSV propios; los
  errores de archivo y de formato incluyen la ruta y la línea.

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

`python pruebas/test_proyecto.py` ejecuta las cuatro suites:

| Suite | Archivo | Pruebas |
|---|---|---|
| Front-end (léxico y sintáctico) | `test_front.py` | 28 |
| Biblioteca propia de datos | `test_datos.py` | 35 |
| Evaluador de expresiones propio | `test_expresiones.py` | 14 |
| Runtime propio (programas completos) | `test_runtime.py` | 28 |

Total: **105 pruebas**. Cubren: CSV válido, vacío, con encabezados, con
faltantes, con comillas y separadores raros; selección, filtrado,
comparaciones, orden (incluido el caso `nada`), duplicados, vacíos,
conversiones; expresiones aritméticas con precedencia y asociatividad,
lógicos, `nada`, errores de tipos y de operación; asignaciones, variables
inexistentes, columnas inexistentes, agregaciones, funciones con
recursión, condicionales, guardado y programas válidos/inválidos.
Ninguna prueba usa bibliotecas externas para el trabajo que se prueba.

---

## 9. Dependencias

| Nombre | Versión | Uso | Por qué está permitida | Qué reemplazaría si se eliminara |
|---|---|---|---|---|
| `antlr4-python3-runtime` | 4.13.2 | ejecutar el lexer/parser generados desde `Arepa.g4` | ANTLR4 la especifica el enunciado del curso | todo el reconocimiento léxico y sintáctico |

No hay más dependencias. En particular: no hay pandas, NumPy,
Matplotlib, Polars, tabulate, openpyxl ni equivalentes, ni en el código
ni en los planes de las siguientes fases.
