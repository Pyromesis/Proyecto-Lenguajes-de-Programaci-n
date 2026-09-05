# AREPA

## Integrantes

* Camilo Bernal
* Diego Moreno
* Yeisson Rincon

## Qué es AREPA

AREPA significa **A**nálisis **R**eproducible de datos **E**scrito con
**P**alabras **A**utóctonas: un lenguaje de dominio específico (DSL) cuyo
vocabulario sale del español hablado en Colombia, para describir flujos de
ciencia de datos (cargar CSV, filtrar, calcular, resumir y graficar) en un
solo programa legible.

Proyecto de la materia *Lenguajes de Programación y Transducción*
(Universidad Sergio Arboleda, 2026-2). El front-end se genera con **ANTLR4**
(herramienta exigida por el curso) y la biblioteca del lenguaje está
implementada desde cero por el equipo.

## Qué problema resuelve

Un analista que no programa en Python tiene que escribir scripts completos
para hacer el mismo flujo una y otra vez: leer un CSV, limpiarlo, calcular
columnas, resumir y graficar. AREPA describe ese flujo como una receta
declarativa:

```text
ventas = monte "datos/ventas.csv" con encabezado, separador ","

limpias = ventas
|> escoja [fecha, ciudad, unidades, precio]
|> deje donde unidades > 0 y precio > 0
|> cree total = unidades * precio

resumen = limpias
|> junte por [ciudad]
|> resuma ingreso = sume(total), registros = cuente()

pinte barras resumen
titulo "Ingresos por ciudad"
ejex ciudad
ejey ingreso
guardela "salidas/ingresos_ciudad.png"

guarde resumen como "salidas/resumen.csv"
chao
```

## Estado exacto del Primer Corte

**Implementado y verificado (Corte 1 — Especificación y front-end):**

* especificación completa: alcance, usuarios, casos de uso, catálogo de
  instrucciones, gramática BNF/EBNF;
* gramática ANTLR4 (`gramatica/Arepa.g4`) con lexer, parser y Visitor
  generados para Python;
* reconocimiento de programas `.arepa`: asignaciones, expresiones con
  precedencia, carga CSV (`monte`), selección (`escoja`), filtros
  (`deje donde`), visualización (`pinte ...`), condicionales y funciones;
* árbol de análisis legible (`--arbol`) y tabla de tokens (`--tokens`);
* diagnóstico de errores léxicos y sintácticos en español con línea y
  columna;
* CLI con códigos de salida 0/1/2 y 161 pruebas en 6 suites.

**Solamente sintáctico en esta fase:** `pinte` y `guardela`/`muestrela` se
reconocen y se validan (tabla y columnas existentes) pero **no generan
imágenes**. Con `--ejecutar`, el programa corre sobre la biblioteca propia
(Tabla, lector CSV, evaluador, símbolos), lo que sirve de evidencia de que
el front-end reconoce de verdad; el procesamiento completo y las gráficas
PNG corresponden a los cortes 2 y 3.

**No pertenece a esta fase:** motor de gráficas, exportación PNG,
estadísticas avanzadas y producto final.

## Instalación

```bash
# 1. Python 3.11 o superior (probado con 3.13)
python --version

# 2. Instalar el único runtime necesario
pip install -r requirements.txt
```

## Dependencias

| Dependencia | Versión | Uso |
|---|---|---|
| Python | 3.11+ (probado 3.13) | lenguaje anfitrión |
| `antlr4-python3-runtime` | 4.13.2 | ejecutar el lexer/parser generados |

ANTLR4 es la única dependencia y está permitida explícitamente por el
curso. Toda la lógica del DSL (Tabla, CSV, expresiones, símbolos, errores)
es propia: sin pandas, NumPy, Matplotlib ni equivalentes.

## Ejecución

```bash
# Validar un programa (front-end: léxico + sintáctico)
python src/cli/main.py ejemplos/demo.arepa

# Ejecutarlo con la biblioteca propia
python src/cli/main.py ejemplos/demo.arepa --ejecutar

# Ver el árbol de análisis
python src/cli/main.py ejemplos/demo.arepa --arbol

# Ver la tabla de tokens
python src/cli/main.py ejemplos/demo.arepa --tokens

# Códigos de salida: 0 = válido, 1 = con errores, 2 = archivo no encontrado
```

## Tokens importantes

* **Estructura**: `quihubo` abre el programa, `chao` lo cierra; el salto de
  línea separa sentencias.
* **Datos**: `monte` (cargar CSV), `guarde ... como ...` (exportar),
  `escoja [...]`, `deje donde`, `cree`, `acomode`, `limpie`, `convierta`,
  `junte por`, `resuma`.
* **Visualización**: `pinte barras|lineas|histograma|dispersion|cajas`,
  cláusulas `titulo`, `ejex`, `ejey`, `leyenda` y cierre `guardela` /
  `muestrela`.
* **Operadores**: `+ - * / % ^`, comparaciones `== != < <= > >=`, lógicos
  `y`, `o`, `no`, pipeline `|>`, flecha `->`, asignación `=`.
* **Literales**: enteros (`42`), decimales (`3.14`), cadenas con escapes
  (`"dice \"hola\""`), booleanos (`obvio`/`falso`) y faltante (`nada`).
* **Comentarios**: `#` hasta fin de línea, permitidos en cualquier posición.

Lista completa: `docs/02_catalogo_instrucciones.md` (51 reservadas y 22
símbolos) y tabla de tokens con `--tokens`.

## Gramática

La fuente única es `gramatica/Arepa.g4` (gramática combinada lexer+parser).
La especificación formal equivalente está en `docs/03_gramatica_ebnf.md`.
Para regenerar:

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

Requiere Java 11+ y `antlr-4.13.2-complete.jar`. En Windows también sirve
`generar_gramatica.bat` (busca el jar en `%USERPROFILE%\antlr\` o usa
`ANTLR_JAR`). El código generado vive en `generado/` y no se edita a mano.

## Árbol de análisis

```bash
python src/cli/main.py ejemplos/demo.arepa --arbol
```

Salida (extracto real):

```text
Árbol de análisis:
`-- programa
    |-- 'quihubo'
    |-- sentencias
    |   |-- sentencia
    |   |   `-- asignacion
    |   |       |-- identificador
    |   |       |   `-- 'ventas'
    |   |       |-- '='
    |   |       `-- expresion
```

## Pruebas

```bash
python pruebas/test_proyecto.py
```

Ejecuta las 6 suites (161 pruebas): front-end (43: 8 positivos, 17
negativos, 10 de diagnóstico, 8 de CLI), estructura del árbol (19), datos
(42), expresiones (14), símbolos y contexto (15) y runtime (28). Cada
suite también corre sola, por ejemplo `python pruebas/test_front.py`.

## Errores (ejemplos reales)

Programa con `@` y con una variable llamada `y`:

```text
Encontré 2 problema(s), revisá esto:
  [léxico] Línea 2, Columna 6: Hay un símbolo '@' que no hace parte del lenguaje AREPA
  [sintáctico] Línea 2, Columna 0: No esperaba 'y' por ahí; revisá si sobra. En esa posición se esperaba 'chao', 'guarde', 'pinte', 'invente', 'devuelva', 'fijese_si', entre otras opciones. Ojo: el operador lógico 'y' (conjunción) es una palabra reservada, no puede usarse como nombre de variable; escogé otro nombre.
```

Programa con un tipo de gráfica inválido:

```text
  [sintáctico] Línea 5, Columna 6: Hace falta 'barras', 'lineas', 'histograma', 'dispersion', 'cajas' cerca de 'pastel'
```

## Estructura del repositorio

```text
proyecto/
├── gramatica/Arepa.g4        gramática ANTLR4 (fuente única)
├── generado/                 lexer, parser y Visitor generados (no editar)
├── src/
│   ├── lenguaje/             analizador, árbol y diagnóstico del front-end
│   ├── datos/                propia: Tabla, Columna, Fila, CSV, tipos
│   ├── expresiones/          propia: operadores y evaluador
│   ├── runtime/              propia: símbolos, contexto y ejecutor
│   ├── errores_base.py       jerarquía propia de errores
│   └── cli/main.py           CLI (validar y --ejecutar)
├── datos/                    CSV de ejemplo para los programas
├── ejemplos/                 demo + filtros + graficas + funciones
├── pruebas/                  6 suites (161) + programas positivos/negativos
├── docs/                     alcance, catálogo, EBNF, informe, arquitectura
├── generar_gramatica.bat     regeneración en Windows
└── requirements.txt          antlr4-python3-runtime==4.13.2
```

## Implementaciones desarrolladas desde cero

Detalle completo en `docs/05_arquitectura.md` (incluye matriz de
trazabilidad funcionalidad → archivo → función → prueba):

* estructura de datos `Tabla` con `Columna` y `Fila` (selección, filtrado,
  ordenamiento por mezcla propio, inserción/eliminación, duplicados,
  vacíos, conversiones, agrupamiento, formato legible);
* lector CSV propio (máquina de estados: comillas, escape `""`,
  separador configurable, errores con línea del archivo);
* escritor CSV propio;
* sistema de tipos propio (conversiones y calendario de fechas propio);
* evaluador de expresiones propio (precedencia, paréntesis, `nada`);
* operadores propios con validación de tipos;
* tabla de símbolos propia (ámbitos, closures con recursión);
* contexto de ejecución propio (salida formateada, registro de errores);
* sistema de errores propio (léxicos, sintácticos, semánticos, de datos);
* agregaciones propias (`cuente`, `sume`, `promedie`, `mediana`, `minimo`,
  `maximo`, `desviacion`) usadas solo como evidencia de reconocimiento.

## Ejemplos

| Ejemplo | Qué demuestra |
|---|---|
| `ejemplos/demo.arepa` | flujo completo del lenguaje |
| `ejemplos/filtros.arepa` | carga, selección, filtros, limpieza y orden |
| `ejemplos/graficas.arepa` | los cinco tipos de visualización (sintáctico) |
| `ejemplos/funciones.arepa` | `invente`, condicionales y `cuenteme` |

Todos validan con `python src/cli/main.py ejemplos/<nombre>.arepa` y corren
con `--ejecutar`.

## Documentación

* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)
* [Arquitectura e implementaciones propias](docs/05_arquitectura.md)
* [Guía de sustentación](docs/07_guia_sustentacion.md)
* [Matriz de trazabilidad del Primer Corte](docs/06_matriz_trazabilidad_corte1.md)
