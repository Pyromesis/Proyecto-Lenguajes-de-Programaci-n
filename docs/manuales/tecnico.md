# AREPA — Manual técnico

Documento de referencia para quien mantiene o extiende el intérprete. Explica
cómo está organizado el código, cómo funciona la cadena completa (gramática →
árbol → Visitor → datos → gráficas) y cómo añadir una instrucción o un tipo de
gráfica. Todas las referencias `archivo:línea` corresponden al estado del
repositorio en la entrega del Corte 3.

* Versión: `AREPA v0.4 (Fase 3 - visualizacion y producto final)`.
* Documentos relacionados: `docs/05_arquitectura.md` (algoritmos y matriz de
  trazabilidad), `docs/09_reglas_semanticas.md` (semántica), `docs/11_informe_fase3.md`
  (informe del motor gráfico), `usuario.md` (uso).

---

## 1. Arquitectura por capas

El proyecto separa gramática, código generado, front-end, biblioteca propia,
interfaz, pruebas, ejemplos y documentación.

```text
gramatica/Arepa.g4        fuente única (lexer + parser ANTLR4)
generado/                 código ANTLR (no editar a mano)
src/
├── lenguaje/             FRONT-END (ANTLR autorizado + lógica propia)
│   ├── analizador.py     analizar() -> (parser, árbol, errores)
│   ├── errores.py        listener propio: traduce diagnósticos a español
│   └── arbol.py          impresión jerárquica del árbol
├── datos/                BIBLIOTECA PROPIA DE DATOS
│   ├── tipos.py          valores, conversiones y calendario propio
│   ├── fila.py, columna.py
│   ├── lista.py, registro.py, acceso.py        (estructuras y acceso 1-based)
│   ├── tabla.py          estructura central y sus operaciones
│   ├── lector_csv.py     máquina de estados CSV propia
│   └── escritor_csv.py   escritura CSV propia
├── expresiones/
│   ├── operadores.py     aritméticos, relacionales y lógicos con tipos
│   └── evaluador.py      EvaluadorExpresiones(ArepaVisitor)
├── runtime/
│   ├── simbolos.py       TablaSimbolos, FuncionArepa
│   ├── contexto.py       ContextoEjecucion (salida, tablas, errores, archivos)
│   └── ejecutor.py       EjecutorArepa(ArepaVisitor): intérprete
├── graficas/             MOTOR GRÁFICO PROPIO (Fase 3)
│   ├── png.py            PNG: chunks, CRC-32, Adler-32, DEFLATE fijo + LZ77
│   ├── fuente.py         fuente bitmap 5x7 propia
│   ├── lienzo.py         búfer RGB y primitivas rasterizadas a mano
│   ├── escalas.py        EscalaLineal, EscalaBanda, ticks "bonitos"
│   └── tipos_grafica.py  Serie, Grafica, los cinco dibujos y la estadística
├── errores_base.py       jerarquía propia de errores
└── cli/main.py           interfaz de línea de comandos
```

**Dependencias entre capas** (de abajo hacia arriba):
`errores_base` → `datos` → `expresiones` → `runtime` → `cli`. El motor gráfico
depende solo de `errores_base` (y de la biblioteca estándar); `runtime` lo usa
desde el ejecutor. Solo `lenguaje/` toca el runtime de ANTLR4. Ni `datos`,
ni `expresiones`, ni `graficas` importan bibliotecas externas.

### 1.1 Flujo completo de una instrucción

```text
   programa.arepa
        │
        ▼
 ┌──────────────┐   analizar()          ┌───────────────┐
 │  gramatica/  │ ────────────────────▶ │ src/lenguaje/ │  listener de errores
 │  Arepa.g4    │  ANTLR lexer+parser   │ analizador.py │  (errores.py)
 └──────┬───────┘                       └───────┬───────┘
        │ generado/ (Lexer, Parser, Visitor)    │ árbol + errores
        ▼                                        ▼
 ┌──────────────┐                        ┌───────────────┐
 │  src/cli/    │  --arbol/--tokens      │  árbol de     │
 │  main.py     │ ◀──────────────────────│  análisis     │
 └──────┬───────┘                        └───────┬───────┘
        │ --ejecutar                             │
        ▼                                        ▼
 ┌────────────────────────────────────────────────────────┐
 │  src/runtime/ejecutor.py  (EjecutorArepa, Visitor)     │
 │    ├── asignaciones/funciones/ciclos → simbolos.py     │
 │    ├── expresiones                    → evaluador.py   │
 │    ├── pipeline y agregaciones        → datos/tabla.py │
 │    ├── monte/guarde                   → lector/escritor │
 │    └── pinte                          → graficas/      │
 └───────────────┬───────────────────────────┬────────────┘
                 │ cuenteme                  │ guardela
                 ▼                           ▼
        salida del programa          PNG / CSV en disco
```

---

## 2. Gramática y regeneración

* Fuente única: `gramatica/Arepa.g4` (527 líneas), gramática **combinada**
  lexer + parser para ANTLR 4.13.2.
* Especificación formal equivalente: `docs/03_gramatica_ebnf.md`.
* Regla inicial: `programa : NL* QUIHUBO NL+ sentencias? NL* CHAO NL* EOF`
  (`Arepa.g4:38`).
* El vocabulario tiene **57 reglas** y **65 palabras reservadas**.

Sincronía verificable:

```bash
python3 herramientas/chequeo_gramatica.py
# Sincronizado: 57/57 reglas y 65 reservadas.
```

Regeneración (requiere **Java 11+** y el jar de ANTLR 4.13.2):

```bash
chmod +x generar_gramatica.sh
./generar_gramatica.sh
# o directamente:
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

El código generado vive en `generado/` (`ArepaLexer.py`, `ArepaParser.py`,
`ArepaVisitor.py`, tablas `.tokens`/`.interp`) y **no se edita a mano**. La
versión del runtime debe coincidir (`antlr4-python3-runtime==4.13.2` en
`requirements.txt`).

---

## 3. Front-end y Visitor

* `src/lenguaje/analizador.py::analizar` (línea 30) crea el lexer y el parser
  de ANTLR, les instala el listener propio (`src/lenguaje/errores.py`,
  `ErroresArepa`, línea 17) y devuelve `(parser, árbol, errores)` sin detenerse
  ante errores.
* `src/lenguaje/errores.py::_traducir` (línea 222) convierte los mensajes
  técnicos de ANTLR a español: traduce nombres de tokens
  (`_traducir_token`, línea 160), recorta el conjunto de opciones a seis
  (`_traducir_conjunto`, línea 191) y añade una pista cuando se usa una palabra
  reservada como variable (`_pista_reservada`, línea 208).
* `src/lenguaje/arbol.py::imprimir_arbol` (línea 46) recorre el árbol con ramas
  ASCII y oculta los saltos de línea.

El intérprete es un **Visitor**:

* `src/runtime/ejecutor.py::EjecutorArepa(ArepaVisitor)` (línea 92) recorre el
  programa.
* `src/expresiones/evaluador.py::EvaluadorExpresiones(ArepaVisitor)` (línea 81)
  calcula expresiones. El evaluador **no** usa `eval()`/`exec()`: la
  precedencia ya está codificada en la forma del árbol por la gramática. Para
  las expresiones que pueden ser un pipeline completo, delega en el callback
  `evaluar_expresion` que le pasa el ejecutor.

---

## 4. Tabla de símbolos y contexto

* `src/runtime/simbolos.py::TablaSimbolos` (línea 53): ámbitos encadenados
  hijo → padre; `declarar` escribe en el ámbito actual y `buscar`/`asignar`
  suben por la cadena. `x = valor` declara si no existe en ningún ámbito visible
  y asigna si existe.
* `src/runtime/simbolos.py::FuncionArepa` (línea 113): guarda el cuerpo de una
  función `invente` y el ámbito donde se definió (closure), lo que permite
  recursión.
* `src/runtime/simbolos.py::validar_identificador` (línea 30): letra Unicode
  (ñ, tildes) o `_` al inicio.
* `src/runtime/contexto.py::ContextoEjecucion` (línea 83): estado global —
  símbolos raíz, salida de `cuenteme`, tablas y registro de errores y de
  archivos generados. El formato de valores y tablas en texto es propio
  (`a_texto`, línea 30), reemplazando a `tabulate`.

Solo las funciones crean ámbito; `fijese_si`, los ciclos y `recorra` no.

---

## 5. Datos propios

* `src/datos/tabla.py::Tabla` (línea 35): lista de `Columna` + lista de `Fila`
  con operaciones propias (`seleccionar`, `filtrar`, `ordenar` con merge sort
  propio y estable, `crear_columna`, `quitar_duplicados`, `rellenar_vacios`,
  `agrupar`, `desde_filas`, `fila_como_registro`, `poner_celda`, `poner_fila`).
* `src/datos/lista.py` / `registro.py`: estructuras propias (sin `dict` ni
  `collections`); `acceso.py` centraliza la lectura/escritura **1-based**
  (`obtener`, `asignar`, `valores_para_fila`).
* `src/datos/lector_csv.py::LectorCSV` (línea 30): máquina de estados con
  comillas, escape `""`, separador configurable y BOM tolerado
  (`utf-8-sig`). `src/datos/escritor_csv.py::EscritorCSV` (línea 24): escritura
  CSV UTF-8 sin BOM.
* `src/datos/tipos.py`: valores del DSL (`nada`, `infinito`), conversiones y
  calendario gregoriano propio (año bisiesto con regla 100/400).

Detalle de algoritmos y limitaciones: `docs/05_arquitectura.md` §2–§4.

---

## 6. Motor gráfico propio

El motor vive en `src/graficas/` y se apoya solo en la biblioteca estándar
(`math`, `os`, `struct`, `unicodedata`).

### 6.1 Formato PNG (`png.py`)

| Elemento | Función (línea) |
|---|---|
| Firma + chunks IHDR/IDAT/IEND | `codificar_png` (523), `_chunk` (456) |
| CRC-32 con tabla propia | `crc32` (78), `_construir_tabla_crc` (61) |
| Adler-32 (zlib) | `adler32` (94) |
| Envoltura del flujo comprimido | `_envolver_deflate` (447) |
| Filtro 0 por fila | `_armar_scanlines` (507) |
| DEFLATE fijo (Huffman BTYPE=01) | `_comprimir_fijo` (392) |
| DEFLATE guardado (BTYPE=00) | `_comprimir_guardado` (418) |
| LZ77 voraz + hash de 3 bytes | `_BuscadorLz77` (322) |
| Escritura y lectura de cabecera | `escribir_png` (561), `leer_cabecera` (577) |

Constantes: profundidad 8, color RGB (tipo 2), compresión 0, filtro 0,
entrelazado 0 (`_PROFUNDIDAD`…`_INTERLACE_NINGUNO`, líneas 44-48). El modo por
defecto es Huffman fijo; el modo guardado existe como alternativa verificable.
No se implementan los filtros 1-4 ni los bloques dinámicos (BTYPE=10).

### 6.2 Lienzo (`lienzo.py`)

`Lienzo` (línea 100) es un `bytearray` RGB. Primitivas: `poner` (149), `linea`
(Bresenham con grosor por sello, 160), `rectangulo` (191), `rectangulo_relleno`
(202), `circulo_relleno` (por filas con `math.isqrt`, sin coma flotante, 209) y
`texto` (255). Todo trazo se recorta contra los bordes; no hay antialiasing.
`pixeles` (287) entrega `bytes` y `guardar` (297) codifica a PNG.

### 6.3 Fuente (`fuente.py`)

Fuente bitmap 5x7: `ANCHO = 5`, `ALTO = 7`, `SEPARACION = 1` (líneas 39-41).
`GLIFOS` (línea 184) tiene un glifo por carácter ASCII imprimible;
`normalizar_texto` (220) quita tildes y diéresis con NFD y un mapa propio
`_ESPECIALES`; el glifo de reemplazo es `?`. `filas` (269), `ancho_texto`
(287) y `alto_texto` (303) los consume el lienzo y el motor.

### 6.4 Escalas (`escalas.py`)

* `EscalaLineal` (154): mapeo afín dominio → rango, inverso y `ticks` con pasos
  "bonitos" (`paso_bonito`, 92). Dominio degenerado se expande.
* `EscalaBanda` (226): categorías en bandas iguales, centro de banda para
  barras y cajas.
* `formatear` (119): número a etiqueta legible.

### 6.5 Tipos de gráfica (`tipos_grafica.py`)

`TIPOS = ("barras", "lineas", "histograma", "dispersion", "cajas")` (línea 54),
paleta propia (`PALETA`, 56) y márgenes fijos (67-70). Las clases `Serie` (274)
y `Grafica` (400) construyen el marco (título, ejes, rejilla, leyenda) y los
cinco dibujos: `_dibujar_barras` (679), `_dibujar_lineas` (752),
`_dibujar_histograma` (794), `_dibujar_dispersion` (862), `_dibujar_cajas`
(898). `cuartiles` (326) y `cubetas_histograma` (355) exponen la estadística
para las pruebas. La función de entrada es `dibujar(tipo, series, **opciones)`
(1058).

### 6.6 Integración con el runtime

`EjecutorArepa.visitInstruccion_grafica` (`src/runtime/ejecutor.py:502`) hace
toda la orquestación: valida la tabla y las columnas, aplica los valores por
defecto, construye las `Serie`, llama a `dibujar(..., ancho=800, alto=480)` y
cierra con `guardela` o `muestrela`. Auxiliares clave: `_columnas_de_clausula`
(749), `_indice_columna` (760), `_primera_columna_categorica` (774),
`_es_numerica` (782), `_columnas_numericas` (816), `_validar_eje_x` (825),
`_guardar_png` (847) y `_abrir_grafica` (863). Los fallos propios del dibujo y de la
escritura lanzan `ErrorGrafica` (`src/errores_base.py:83`); una variable
inexistente sigue siendo `ErrorVariable` y una columna inexistente,
`ErrorColumna`.

---

## 7. CLI (`src/cli/main.py`)

* `main` (línea 121) define los argumentos: `--ayuda/--help/-h`, `--version`,
  `--arbol`, `--tokens`, `--ejecutar` y `--sin-ventana` (que fija
  `AREPA_SIN_VENTANA=1`, líneas 176-177).
* `_ejecutar` (231) corre el programa con el runtime propio.
* `_mostrar_contexto` (74) imprime el fragmento de la línea con el caret `^`.
* `_resumen_archivos` (105) imprime el bloque final `Archivos generados:` con
  ruta, tipo y bytes, a partir del registro del `ContextoEjecucion`.
* Códigos de salida: 0 (válido), 1 (con errores), 2 (archivo no encontrado).

---

## 8. Manejo de errores

Jerarquía propia en `src/errores_base.py`:

```text
ErrorArepa
├── ErrorSemantico ── ErrorVariable, ErrorColumna, ErrorTipos, ErrorOperacion
└── ErrorEjecucion ── ErrorArchivo ── ErrorCSV
                   └─ ErrorGrafica
```

Cada error lleva `mensaje`, `linea`, `columna` y `contexto`. Los errores
léxicos y sintácticos los produce el listener del front-end; los semánticos y
de ejecución, el runtime y el motor gráfico. Se reportan **en español, con
línea y columna**, y la CLI añade el caret. Los errores descubiertos sobre
datos (por ejemplo, una celda que no convierte) llevan la línea exacta del
archivo de datos, aunque la línea del programa es aproximada.

Las señales internas de control de flujo (`RetornoFuncion`, `SalirCiclo`,
`SeguirCiclo`) **no** son errores: viajan como excepciones y el ejecutor las
convierte en error semántico solo si escapan de su contexto.

---

## 9. Pruebas

* Corredor maestro: `pruebas/test_proyecto.py` (8 suites).
* **319 pruebas** en total; el conteo canónico está en
  `herramientas/chequeo_pruebas.py`.

| Suite | Archivo | Pruebas |
|---|---|---:|
| Front-end | `test_front.py` | 55 |
| Árbol | `test_arbol.py` | 28 |
| Datos | `test_datos.py` | 43 |
| Estructuras | `test_estructuras.py` | 48 |
| Expresiones | `test_expresiones.py` | 16 |
| Símbolos | `test_simbolos.py` | 15 |
| Runtime | `test_runtime.py` | 51 |
| Gráficas | `test_graficas.py` | 63 |

```bash
.venv/bin/python herramientas/chequeo_pruebas.py   # 8 suites, 319 pruebas
python3 herramientas/chequeo_gramatica.py          # 57/57 reglas, 65 reservadas
```

La suite de gráficas cubre el codificador PNG (20), la fuente (3), el lienzo
(7), las escalas (4), los cinco dibujos y regresiones de ejes (14), la
integración con el runtime (11) y el caso de estudio (4).

---

## 10. Cómo extender

### 10.1 Añadir una instrucción

1. **Gramática**: añade la regla en `gramatica/Arepa.g4` y enlázala desde
   `sentencia` (o desde `operacion_datos` si es una etapa de pipeline). Si
   agrega palabras reservadas, declara sus tokens en el lexer **antes** de la
   regla de identificadores.
2. **Regenerar**: `./generar_gramatica.sh` (requiere Java 11+).
3. **EBNF**: replica la producción en `docs/03_gramatica_ebnf.md` con el mismo
   nombre de no terminal y añade la palabra reservada a `PALABRA_RESERVADA`.
4. **Comprobar sincronía**: `python3 herramientas/chequeo_gramatica.py` debe dar
   57/57 → ahora N/N reglas y las reservadas nuevas.
5. **Ejecutor**: implementa `visit<Regla>` en `src/runtime/ejecutor.py`
   (o en el evaluador si es una expresión). Usa `ContextoEjecucion` para la
   salida y `TablaSimbolos` para los nombres.
6. **Errores**: usa las clases de `src/errores_base.py`; nunca lances un
   `Exception` genérico.
7. **Catálogo y reglas semánticas**: documenta la instrucción en
   `docs/02_catalogo_instrucciones.md` y `docs/09_reglas_semanticas.md`.
8. **Pruebas**: añade un programa positivo/negativo en `pruebas/` y casos en la
   suite adecuada; actualiza `ESPERADO` en `herramientas/chequeo_pruebas.py` y
   el conteo en los documentos que lo citan.

### 10.2 Añadir un tipo de gráfica

1. **Gramática**: añade el literal a `tipo_grafica` (`Arepa.g4:229`) y su token
   en el lexer; añade la palabra a `PALABRA_RESERVADA` en la EBNF.
2. **Motor**: añade el nombre a `TIPOS` (`tipos_grafica.py:54`) e implementa
   `_dibujar_<tipo>` (línea aprox. junto a los otros cinco) y su rama en
   `renderizar` (1046). Reutiliza `EscalaLineal`/`EscalaBanda`, `Lienzo` y la
   fuente propia.
3. **Estadística**: si necesitas cálculos nuevos, expón una función pública
   como `cuartiles`/`cubetas_histograma` para poder probarla sin mirar píxeles.
4. **Runtime**: normalmente no hay que tocar `visitInstruccion_grafica`; los
   valores por defecto por tipo sí pueden requerir una rama nueva (por ejemplo,
   el histograma fuerza una sola columna).
5. **Pruebas**: añade un caso de dibujo (PNG válido 800x480) y otro de
   integración desde el DSL, ambos en `pruebas/test_graficas.py`. Actualiza el
   conteo canónico.

---

## 11. Decisiones y limitaciones

* **Sin dependencias externas para la lógica del DSL.** La única externa es
  `antlr4-python3-runtime==4.13.2`, exigida por el curso para el lexer/parser.
* **PNG propio** con profundidad 8, color RGB, filtro 0 y DEFLATE fijo + LZ77;
  no hay filtros 1-4, bloques dinámicos, transparencias ni entrelazado.
* **800x480 fijo**; las gráficas no tienen tamaño configurable ni subtítulos,
  eje secundario o gráficas apiladas.
* **Sin antialiasing** y **tildes simplificadas** en la fuente 5x7 (los
  descendentes g, p, q, y, j se dibujan dentro de la caja).
* **Sin escalas logarítmicas ni de fechas**: las fechas se grafican como texto
  o como índice continuo.
* Determinismo: LZ77 voraz + Huffman fijo y fuente sin aleatoriedad hacen que
  dos ejecuciones produzcan el mismo PNG (verificable con `sha256sum`).

El detalle ampliado de cada limitación está en `docs/11_informe_fase3.md` §4 y
en `docs/05_arquitectura.md`.
