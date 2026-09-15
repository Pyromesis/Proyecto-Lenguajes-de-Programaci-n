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

## Estado exacto (Cortes 1 y 2, Linux-only)

**Corte 1 — Especificación y front-end (verificado):**

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
* CLI con códigos de salida 0/1/2 y 194 pruebas en 6 suites.

**Corte 2 — Semántica y procesamiento de datos (verificado):**

* Visitor y motor propios (`src/runtime/ejecutor.py`,
  `src/expresiones/evaluador.py`), tabla de símbolos y contexto propios;
* carga, selección, filtrado, ordenamiento (merge sort propio), columnas
  calculadas, `limpie`/`renombre`/`convierta`, `junte por` + `resuma`,
  `describa` y `guarde ... como` (escritor CSV propio UTF-8);
* reglas semánticas en `docs/09_reglas_semanticas.md` y trazabilidad en
  `docs/10_matriz_trazabilidad_corte2.md`;
* 3 programas completos con exportación versionada:
  `salidas/resumen_ciudades.csv` (demo),
  `salidas/resumen_ciclos.csv` (ciclos),
  `salidas/filtros_listos.csv` (filtros).

**Solamente sintáctico en esta fase:** `pinte` y `guardela`/`muestrela` se
reconocen y se validan (tabla y columnas existentes) pero **no generan
imágenes** (Fase 3).

**No pertenece a esta fase:** motor de gráficas y exportación PNG.

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

> **Biblioteca externa pública autorizada (única): ANTLR4.**
> El curso exige generar el lexer y el parser con ANTLR4, por eso el
> proyecto usa `antlr4-python3-runtime==4.13.2` (solo para ejecutar el
> lexer/parser generados desde `gramatica/Arepa.g4`; ver
> `requirements.txt`). **Todo lo demás es biblioteca propia del DSL**,
> implementada desde cero por el equipo: `Tabla`/`Columna`/`Fila`, lector
> y escritor CSV, sistema de tipos, operadores y evaluador de expresiones,
> tabla de símbolos, contexto y ejecutor, y sistema de errores
> (detalle en `docs/05_arquitectura.md`).

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

# Ver el árbol de análisis
python3 src/cli/main.py ejemplos/demo.arepa --arbol

# Ver la tabla de tokens
python3 src/cli/main.py ejemplos/demo.arepa --tokens

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

Lista completa: `docs/02_catalogo_instrucciones.md` (59 reservadas y 22
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

Ejecuta las 6 suites (194 pruebas): front-end (48: 9 positivos, 20
negativos, 10 de diagnóstico, 9 de CLI), estructura del árbol (21), datos
(43), expresiones (16), símbolos y contexto (15) y runtime (51). Cada
suite también corre sola, por ejemplo `python3 pruebas/test_front.py`.

El conteo es único y verificable (fuente de verdad):

```bash
python3 herramientas/chequeo_pruebas.py
# Unificado: 6 suites, 194 pruebas.
```

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
│   └── cli/                  main.py (validar y --ejecutar) y repl.py
├── datos/                    CSV de ejemplo para los programas
├── ejemplos/                 demo + filtros + graficas + funciones + ciclos
├── Ejercicios_Problemas/     187 ejercicios (índice en su README.md)
├── salidas/                  evidencia Corte 2 (3 CSV versionados)
├── pruebas/                  6 suites (194) + programas positivos/negativos
├── herramientas/             chequeos, demo de sustentación y consola
├── docs/                     alcance, catálogo, EBNF, informes, arquitectura,
│                             reglas semánticas (09) y trazabilidad Corte 2 (10)
├── generar_gramatica.sh      regeneración en Linux
├── requirements.txt          antlr4-python3-runtime==4.13.2
└── Proyecto_LP.pdf           enunciado del curso
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
  `maximo`, `desviacion`) ejecutadas por `junte`/`resuma` y `describa`.

## Ejemplos

| Ejemplo | Qué demuestra | Exportación |
|---|---|---|
| `ejemplos/demo.arepa` | flujo completo del lenguaje | `salidas/resumen_ciudades.csv` |
| `ejemplos/filtros.arepa` | carga, selección, filtros, limpieza y orden | `salidas/filtros_listos.csv` |
| `ejemplos/graficas.arepa` | los cinco tipos de visualización (sintáctico) | — (validación, PNG en Fase 3) |
| `ejemplos/funciones.arepa` | `invente`, condicionales y `cuenteme` | — |
| `ejemplos/ciclos.arepa` | `mientras`, `repita`, `pare`/`siga` + flujo de datos | `salidas/resumen_ciclos.csv` |

Todos validan con `python3 src/cli/main.py ejemplos/<nombre>.arepa` y corren
con `--ejecutar`. Los 3 CSV de evidencia están versionados (exceptuados en
`.gitignore`).

## Ejercicios

187 programas de práctica en `Ejercicios_Problemas/` (índice completo en
`Ejercicios_Problemas/README.md`): repaso general más 45 nuevos del Corte 2
(F12–F26, M11–M25, D12–D26) y 75 de funciones. Todos validan y ejecutan:

```bash
python3 src/cli/main.py Ejercicios_Problemas/faciles/F12_deje_donde_simple.arepa --ejecutar
```

## Herramientas

```bash
python3 herramientas/chequeo_gramatica.py   # EBNF <-> .g4: 46/46 reglas, 59 reservadas
python3 herramientas/chequeo_pruebas.py     # conteo único: 6 suites, 194 pruebas
bash herramientas/demo_sustentacion.sh      # demo de sustentación paso a paso
```

Autocompletado por Tab (Vim, REPL y Bash): `herramientas/consola/README.md`.

## Documentación

* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)
* [Arquitectura e implementaciones propias](docs/05_arquitectura.md)
* [Informe de la Fase 2 (Semántica y Corte 2)](docs/08_informe_fase2.md)
* [Reglas semánticas (Corte 2)](docs/09_reglas_semanticas.md)
* [Matriz de trazabilidad del Corte 2](docs/10_matriz_trazabilidad_corte2.md)
* [Guía de sustentación](docs/07_guia_sustentacion.md)
* [Matriz de trazabilidad del Primer Corte](docs/06_matriz_trazabilidad_corte1.md)
