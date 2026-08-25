# AREPA

AREPA significa **A**nálisis **R**eproducible de datos **E**scrito con
**P**alabras **A**utóctonas. Es un DSL cuyo vocabulario sale del español que
se habla a diario en Colombia, pensado para tareas de ciencia de datos y
visualización.

Este es el proyecto de la materia *Lenguajes de Programación y Transducción*
(Universidad Sergio Arboleda, 2026-2). El front-end se genera con **ANTLR4**
(herramienta autorizada por el curso) y **toda la biblioteca del lenguaje —
estructuras de datos, lector CSV, evaluador de expresiones, tabla de
símbolos y sistema de errores — está implementada desde cero por el
equipo**, sin pandas, NumPy, Matplotlib ni bibliotecas equivalentes.

## Un programa de ejemplo

```text
# demo.arepa
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

guarde resumen como "salidas/resumen.csv"
chao
```

## Cómo probarlo

```bash
pip install -r requirements.txt

# Validar un programa (análisis léxico y sintáctico)
python src/cli/main.py ejemplos/demo.arepa

# Ejecutarlo con la biblioteca propia (carga CSV, pipeline, agregaciones)
python src/cli/main.py ejemplos/demo.arepa --ejecutar

# Ver el árbol de análisis o los tokens
python src/cli/main.py ejemplos/demo.arepa --arbol
python src/cli/main.py ejemplos/demo.arepa --tokens

# Correr TODAS las suites (127 pruebas)
python pruebas/test_proyecto.py
```

La salida al ejecutar el demo se ve así:

```text
==============================================================
 AREPA v0.2 (Fase 1 - front-end + biblioteca propia)
==============================================================
Archivo : ejemplos/demo.arepa
Análisis léxico   : OK (166 tokens)
Análisis sintáctico: OK
¡Quihubo pues! Programa bien escrito: 9 sentencia(s) reconocida(s).

--------------------------------------------------------------
 Ejecución con la biblioteca propia
--------------------------------------------------------------
[guarde] La tabla 'resumen' quedó escrita en 'salidas/resumen.csv' (3 filas).

¡De una! El programa corrió completo sin tropiezos.
```

## Qué hay en cada carpeta

| Ruta | Contenido |
|---|---|
| `gramatica/Arepa.g4` | la gramática ANTLR4 del lenguaje (fuente única) |
| `generado/` | lexer y parser en Python que produce ANTLR |
| `src/lenguaje/` | orquestación del front-end, árbol y diagnóstico |
| `src/datos/` | biblioteca propia: Tabla, Columna, Fila, lector y escritor CSV, tipos |
| `src/expresiones/` | biblioteca propia: operadores y evaluador de expresiones |
| `src/runtime/` | biblioteca propia: símbolos, contexto y ejecutor del DSL |
| `src/cli/main.py` | interfaz de línea de comandos |
| `datos/` | CSV de ejemplo que consumen los programas |
| `pruebas/` | 5 suites de pruebas y programas positivos/negativos |
| `ejemplos/` | demo completo y ejemplos cortos por componente |
| `docs/` | alcance, catálogo, EBNF, informe y arquitectura |

## Implementaciones propias

Todo esto está escrito desde cero por el equipo (ver `docs/05_arquitectura.md`
para los algoritmos):

* **Estructura de datos `Tabla`** con `Columna` y `Fila` propias:
  selección, filtrado, ordenamiento por mezcla (merge sort propio),
  creación y renombre de columnas, eliminación de duplicados, tratamiento
  de `nada`, conversión de tipos, agrupamiento y formato en texto.
* **Lector CSV propio**: máquina de estados carácter a carácter con
  comillas, escape `""`, separador configurable, encabezados opcionales,
  líneas vacías, campos faltantes y errores con número de línea.
* **Escritor CSV propio** para `guarde ... como ...`.
* **Sistema de tipos propio**: detección, conversión y validación
  (incluye calendario propio para fechas AAAA-MM-DD con bisiestos).
* **Evaluador de expresiones propio** que recorre el árbol de ANTLR:
  aritmética, relacionales, lógicos, precedencia, paréntesis, cadenas con
  escapes y propagación del valor faltante `nada`.
* **Operadores propios** con validación de tipos y errores comprensibles.
* **Tabla de símbolos propia** con ámbitos encadenados y funciones
  `invente` como closures (admiten recursión).
* **Contexto de ejecución propio** con salida formateada sin `tabulate`.
* **Sistema de errores propio** (`errores_base.py`): semánticos, de
  tipos, columnas, variables, archivos, CSV y ejecución, con línea,
  columna, contexto y mensaje en español.
* **Agregaciones propias**: `cuente`, `sume`, `promedie`, `mediana`
  (orden por inserción propio), `minimo`, `maximo`, `desviacion`
  (estándar poblacional).
* **Diagnóstico del front-end propio**: listener que traduce los
  mensajes técnicos de ANTLR a español con pistas útiles.

Lo único que NO es propio es el runtime de ANTLR4, autorizado por el
enunciado del curso para el lexer y el parser.

## Ejemplos

* `ejemplos/demo.arepa` — flujo completo: carga, preparación, resumen, gráfica y exportación.
* `ejemplos/filtros.arepa` — carga, selección, filtros, limpieza y orden.
* `ejemplos/graficas.arepa` — los cinco tipos de gráfica con sus cláusulas.
* `ejemplos/funciones.arepa` — funciones con `invente`, condicionales y `cuenteme`.

Todos se ejecutan con `python src/cli/main.py ejemplos/<nombre>.arepa --ejecutar`.

## Documentación

* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)
* [Arquitectura e implementaciones propias](docs/05_arquitectura.md)

## Regenerar la gramática (opcional)

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

Hace falta Java 11 y el jar `antlr-4.13.2-complete.jar`.
Otra opción es `pip install antlr4-tools` y dejar que descargue lo necesario.
En Windows también sirve el script `generar_gramatica.bat`, que busca el jar
en `%USERPROFILE%\antlr\` o toma la ruta de la variable `ANTLR_JAR`.
