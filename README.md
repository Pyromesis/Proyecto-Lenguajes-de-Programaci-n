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
quihubo
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

guarde resumen como "salidas/resumen_ciudades.csv"
chao
```

Es `ejemplos/demo.arepa` (completo con `cuenteme`, `fijese_si` e `invente`).

Además del pipeline sobre CSV, AREPA puede construir estructuras propias
en memoria (listas, registros y tablas), recorrerlas y agregarlas sin
llamar a ninguna biblioteca externa:

```text
quihubo
gastos = arme [mes, categoria, valor] con [
    ["Enero", "Mercado", 120000],
    ["Enero", "Transporte", 45000],
    ["Febrero", "Mercado", 135000]
]

total = sume(gastos, valor)          # agregación fuera de 'resuma'
recorra fila en gastos {             # recorrido con registro de fila
    cuenteme fila["mes"], fila["valor"]
}

resumen = gastos
|> junte por [categoria]
|> resuma total = sume(valor), registros = cuente()

guarde resumen como "salidas/memoria_resumen.csv"
chao
```

Es `ejemplos/memoria.arepa` (completo con listas, registros, acceso
1-based, `agregue`, `saque`, `largo`, `columna` y `columnas`).

## Fases del proyecto

El curso plantea tres cortes acumulativos. Los tres están entregados: el
tercero (gráficas y exportación PNG) se completó en la versión
`AREPA v0.4 (Fase 3 - visualizacion y producto final)`.

| Corte | Fase | Alcance de la versión | Entregables |
|---|---|---|---|
| Primero | Especificación y front-end | Asignaciones y expresiones, carga de CSV, selección de columnas, filtros sencillos y reconocimiento de `pinte` aunque todavía no genere la gráfica | Documento de alcance, catálogo de instrucciones, gramática BNF/EBNF y archivo `.g4`, lexer y parser generados, pruebas léxicas y sintácticas |
| Segundo | Semántica y procesamiento de datos | Visitor, contexto y tabla de símbolos; selección, filtrado, columnas calculadas, agrupamiento, agregaciones y escritura de resultados en CSV | Reglas semánticas documentadas, tres programas completos y pruebas unitarias y de integración |
| Tercero | Visualización y producto final | Cinco tipos de gráficas configurables desde el DSL, exportación a PNG con motor propio, CLI estable (`--sin-ventana`, `--ayuda`, `--version`) y caso de estudio con datos reales | Intérprete completo, manual de usuario y técnico, pruebas de regresión y caso de estudio reproducible |

El enunciado completo está en [`Proyecto_LP.pdf`](docs/Proyecto_LP.pdf), sección 5.

Sobre el Corte 2 se agregó una ampliación **A4**: listas, registros y
tablas en memoria (`arme`), acceso 1-based encadenado, asignación
indexada, `agregue`/`saque`, `recorra` y agregaciones fuera de `resuma`.
Se valida con la suite `test_estructuras.py` (48 pruebas) y con
`ejemplos/memoria.arepa`.

El Corte 3 agregó el **motor gráfico propio** (`src/graficas/`): cinco tipos
de gráfica (`barras`, `lineas`, `histograma`, `dispersion`, `cajas`) y
exportación a PNG RGB 800x480 **sin matplotlib ni PIL** (DEFLATE fijo + LZ77,
CRC-32 y Adler-32 propios). Se valida con la suite `test_graficas.py`
(63 pruebas), con `ejemplos/graficas.arepa` (que ahora genera cinco PNG
reales en `salidas/`) y con el caso de estudio de `caso_estudio/`.

## Requisitos

Entorno oficial del proyecto (Linux-only):

* **Linux** (distribución con terminal Bash)
* **Python 3.11 o superior** (probado con 3.13)
* **Java 11 o superior** (solo para regenerar el lexer/parser con ANTLR)
* **Git**
* **ANTLR 4.13.2** (`antlr-4.13.2-complete.jar` para regenerar;
  `antlr4-python3-runtime==4.13.2` para ejecutar, instalado vía
  `requirements.txt`)

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Pyromesis/Proyecto-Lenguajes-de-Programaci-n.git
cd Proyecto-Lenguajes-de-Programaci-n

# 2. Comprobar versiones
python3 --version   # 3.11+
java -version       # 11+

# 3. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 4. Instalar el único runtime necesario
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Dependencias

| Dependencia | Versión | Uso |
|---|---|---|
| Python | 3.11+ (probado 3.13) | lenguaje anfitrión |
| `antlr4-python3-runtime` | 4.13.2 | ejecutar el lexer/parser generados (única externa) |

Sin pandas, NumPy, Matplotlib ni equivalentes.

## Ejecución

```bash
# Validar un programa (front-end: léxico + sintáctico)
python3 src/cli/main.py ejemplos/demo.arepa

# Ejecutarlo con la biblioteca propia
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar

# Ejecutar y exportar gráficas sin abrir ventanas (útil en CI)
python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar --sin-ventana

# Ver el árbol de análisis
python3 src/cli/main.py ejemplos/demo.arepa --arbol

# Ver la tabla de tokens
python3 src/cli/main.py ejemplos/demo.arepa --tokens

# Ayuda y versión
python3 src/cli/main.py --ayuda
python3 src/cli/main.py --version
# AREPA v0.4 (Fase 3 - visualizacion y producto final)

# Códigos de salida: 0 = válido, 1 = con errores, 2 = archivo no encontrado
```

Consola interactiva (REPL con autocompletado por Tab):

```bash
python3 src/cli/repl.py            # con fantasma (terminal Linux)
python3 src/cli/repl.py --simple   # modo clásico
```

## Tokens importantes

* **Estructura**: `quihubo` abre el programa, `chao` lo cierra; el salto de
  línea separa sentencias.
* **Datos**: `monte` (cargar CSV), `guarde ... como ...` (exportar),
  `escoja [...]`, `deje donde`, `cree`, `acomode`, `limpie`, `convierta`,
  `junte por`, `resuma`.
* **Estructuras propias**: listas `[1, 2]`, registros `{nombre: "Ana"}`,
  tablas `arme [cols] con [[...]]` (o vacías), acceso 1-based encadenado
  (`t[1]["col"]`), asignación indexada, `agregue ... en ...`,
  `saque ... de ...`, `recorra ... en ... { }`, builtins `largo`,
  `columna`, `columnas` y agregaciones fuera de `resuma`
  (`sume(tabla, col)`, `sume(lista)`, `cuente(tabla[, col])`, …).
* **Visualización**: `pinte barras|lineas|histograma|dispersion|cajas`,
  cláusulas `titulo`, `ejex`, `ejey`, `leyenda` y cierre `guardela` /
  `muestrela`.
* **Control**: `fijese_si` / `sino`, `mientras (cond)`, `repita N veces`,
  `repita i desde A hasta B (paso P)`, `pare` (rompe), `siga` (sigue).
* **Operadores**: `+ - * / % ^`, comparaciones `== != < <= > >=`, lógicos
  `y`, `o`, `no`, pipeline `|>`, flecha `->`, asignación `=`.
* **Literales**: enteros (`42`), decimales (`3.14`), cadenas con escapes
  (`"dice \"hola\""`), booleanos (`obvio`/`falso`) y faltante (`nada`).
* **Comentarios**: `#` hasta fin de línea, permitidos en cualquier posición.

Lista completa: `docs/02_catalogo_instrucciones.md` (65 reservadas y 23
símbolos) y tabla de tokens con `--tokens`.

## Gramática

La fuente única es `gramatica/Arepa.g4` (gramática combinada lexer+parser).
La especificación formal equivalente está en `docs/03_gramatica_ebnf.md`.

### ANTLR en Linux

Descargue el jar de ANTLR 4.13.2 y defina `ANTLR_JAR`:

```bash
mkdir -p "$HOME/antlr"
# Descargue antlr-4.13.2-complete.jar desde https://www.antlr.org/download.html
# y guárdelo en $HOME/antlr/, luego:
export ANTLR_JAR="$HOME/antlr/antlr-4.13.2-complete.jar"
```

### Regenerar el lexer/parser

```bash
chmod +x generar_gramatica.sh
./generar_gramatica.sh
```

El script comprueba Java 11+, el jar de ANTLR, la existencia de
`gramatica/Arepa.g4`, crea `generado/` si hace falta y verifica que se
generen `ArepaLexer.py`, `ArepaParser.py` y `ArepaVisitor.py`.

Alternativa con `antlr4-tools` (requiere Java 11+):

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

El código generado vive en `generado/` y no se edita a mano.

## Árbol de análisis

```bash
python3 src/cli/main.py ejemplos/demo.arepa --arbol
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
python3 pruebas/test_proyecto.py
```

Ejecuta las 8 suites (319 pruebas): front-end (55: 10 positivos, 22
negativos, 10 de diagnóstico, 13 de CLI), estructura del árbol (28), datos
(43), estructuras propias (48), expresiones (16), símbolos y contexto (15),
runtime (51) y gráficas (63). Cada suite también corre sola con el
entorno activado, por ejemplo `python3 pruebas/test_estructuras.py`.

El conteo es único y verificable (fuente de verdad):

```bash
python3 herramientas/chequeo_pruebas.py
# Unificado: 8 suites, 319 pruebas.
```

Además, los 170 programas de regresión (164 ejercicios + 6 ejemplos) validan
y ejecutan con `--ejecutar` sin fallos.

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
│   ├── datos/                propia: Tabla, Lista, Registro, Columna, Fila, acceso, CSV, tipos
│   ├── expresiones/          propia: operadores y evaluador
│   ├── runtime/              propia: símbolos, contexto y ejecutor
│   ├── graficas/             propia: motor de gráficas (png, lienzo, fuente, escalas, tipos)
│   ├── errores_base.py       jerarquía propia de errores
│   └── cli/                  main.py (validar y --ejecutar) y repl.py
├── datos/                    CSV de ejemplo para los programas
├── ejemplos/                 6: demo, memoria, filtros, graficas, funciones, ciclos
├── ejercicios/               164 ejercicios por corte (1: 32, 2: 120, 3: 12)
├── caso_estudio/             caso reproducible: programa.arepa + datos/ + 5 PNG + CSV
├── salidas/                  evidencia: CSV versionados y PNG temporales
├── pruebas/                  8 suites (319) + positivos/negativos
├── herramientas/             chequeos, demo de sustentación y consola
├── docs/                     índice (README.md), alcance, catálogo, EBNF,
│                             informes, arquitectura, reglas, manuales y PDF
├── generar_gramatica.sh      regeneración en Linux
└── requirements.txt          antlr4-python3-runtime==4.13.2
```

Cada carpeta trae su `README.md` con el detalle
(`datos/`, `docs/`, `ejemplos/`, `generado/`, `gramatica/`, `herramientas/`,
`pruebas/`, `salidas/`, `src/`, `ejercicios/`).

## Implementaciones desarrolladas desde cero

Detalle completo en `docs/05_arquitectura.md` (incluye matriz de
trazabilidad funcionalidad → archivo → función → prueba):

* estructura de datos `Tabla` con `Columna` y `Fila` (selección, filtrado,
  ordenamiento por mezcla propio, inserción/eliminación, duplicados,
  vacíos, conversiones, agrupamiento, formato legible);
* estructuras propias `Lista` y `Registro`, más `datos/acceso.py` para el
  acceso y la asignación 1-based; `Tabla.desde_filas`,
  `fila_como_registro`, `poner_celda` y `poner_fila` para las tablas en
  memoria;
* builtins propios `largo`, `columna` y `columnas`, y agregaciones en
  memoria fuera de `resuma` (`sume(tabla, col)`, `sume(lista)`, …);
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
  `maximo`, `desviacion`) ejecutadas por `junte`/`resuma` y `describa`;
* motor de gráficas propio (`src/graficas/`): codificador PNG (chunks,
  CRC-32 y Adler-32 propios, DEFLATE fijo + LZ77), lienzo RGB con primitivas
  rasterizadas a mano, fuente bitmap 5x7 y escalas lineales y de banda. Sin
  matplotlib, PIL ni zlib.

## Ejemplos

| Ejemplo | Qué demuestra | Exportación |
|---|---|---|
| `ejemplos/demo.arepa` | flujo completo del lenguaje | `salidas/resumen_ciudades.csv` |
| `ejemplos/memoria.arepa` | listas, registros, `arme`, acceso 1-based, `recorra` y agregaciones en memoria | `salidas/memoria_resumen.csv` |
| `ejemplos/filtros.arepa` | carga, selección, filtros, limpieza y orden | `salidas/filtros_listos.csv` |
| `ejemplos/graficas.arepa` | los cinco tipos de visualización | 5 PNG en `salidas/` |
| `ejemplos/funciones.arepa` | `invente`, condicionales y `cuenteme` | — |
| `ejemplos/ciclos.arepa` | `mientras`, `repita`, `pare`/`siga` + flujo de datos | `salidas/resumen_ciclos.csv` |

Todos validan con `python3 src/cli/main.py ejemplos/<nombre>.arepa` y corren
con `--ejecutar`. Los CSV de `salidas/` están versionados como evidencia
(exceptuados en `.gitignore`); los PNG de `salidas/` son temporales.
`graficas.arepa` genera cinco PNG reales (`salidas/barras.png`,
`ventas_lineas.png`, `histograma.png`, `dispersion.png`, `cajas.png`);
conviene correrlo con `--sin-ventana`. Los PNG del caso de estudio sí se
versionan en `caso_estudio/salidas/`.

## Caso de estudio

`caso_estudio/` cierra el recorrido con datos públicos: la serie mensual de
pasajeros internacionales (AirPassengers, 1949-1960, 144 filas). El programa
`caso_estudio/programa.arepa` carga el CSV, lo limpia, calcula el resumen anual
y genera cinco PNG más un CSV de evidencia:

```bash
AREPA_SIN_VENTANA=1 python3 src/cli/main.py caso_estudio/programa.arepa --ejecutar
```

Indicadores verificados: total 40363, promedio 280.2986, mediana 265.5,
mínimo 104, máximo 622, 1949 = 1520, 1960 = 5714, crecimiento 275.92 % y CAGR
12.79 %. El análisis completo está en `caso_estudio/README.md`.

## Ejercicios

164 programas de práctica en `ejercicios/`, separados por corte (índice
completo en `ejercicios/README.md`):

| Corte | Programas | Contenido |
|---|---:|---|
| 1 | 32 | front-end, expresiones y primer pipeline |
| 2 | 120 | semántica, datos y 75 ejercicios de funciones |
| 3 | 12 | las cinco gráficas, estética y exportación PNG |

Con los 6 de `ejemplos/` suman 170 programas, y todos validan y ejecutan:

```bash
python3 src/cli/main.py ejercicios/corte1/faciles/F01_programa_minimo.arepa --ejecutar
python3 src/cli/main.py ejercicios/corte3/graficas/G01_barras_ciudad.arepa --ejecutar --sin-ventana
bash herramientas/regresion_programas.sh
```

## Herramientas

```bash
python3 herramientas/chequeo_gramatica.py      # EBNF <-> .g4: 57/57 reglas, 65 reservadas
python3 herramientas/chequeo_pruebas.py        # conteo único: 8 suites, 319 pruebas
python3 herramientas/chequeo_documentacion.py  # enlaces, referencias y conteos 32/120/12/6
bash herramientas/regresion_programas.sh       # 170 programas (164 + 6 ejemplos)
bash herramientas/demo_sustentacion.sh         # demo de sustentación paso a paso
```

Autocompletado por Tab (Vim, REPL y Bash): `herramientas/consola/README.md`.

## Documentación

* [Índice completo de documentación](docs/README.md)
* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)
* [Arquitectura e implementaciones propias](docs/05_arquitectura.md)
* [Informe de la Fase 2 (Semántica y Corte 2)](docs/08_informe_fase2.md)
* [Informe de la Fase 3 (Visualización y Corte 3)](docs/11_informe_fase3.md)
* [Reglas semánticas](docs/09_reglas_semanticas.md)
* [Matriz de trazabilidad del Corte 2](docs/10_matriz_trazabilidad_corte2.md)
* [Matriz de trazabilidad del Corte 3](docs/12_matriz_trazabilidad_corte3.md)
* [Manual de usuario](docs/manuales/usuario.md)
* [Manual técnico](docs/manuales/tecnico.md)
* [Guía de sustentación](docs/07_guia_sustentacion.md)
* [Matriz de trazabilidad del Primer Corte](docs/06_matriz_trazabilidad_corte1.md)
