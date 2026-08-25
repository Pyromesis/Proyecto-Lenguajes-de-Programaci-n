# AREPA

AREPA significa **A**nálisis **R**eproducible de datos **E**scrito con
**P**alabras **A**utóctonas. Es un DSL cuyo vocabulario sale del español que
se habla a diario en Colombia, pensado para tareas de ciencia de datos y
visualización.

Este es el proyecto de la materia *Lenguajes de Programación y Transducción*
(Universidad Sergio Arboleda, 2026-2). Todo el front-end está hecho con
ANTLR4 y Python.

En esta primera entrega el sistema ya lee programas `.arepa`, construye el
árbol de análisis y avisa cuando hay errores léxicos o sintácticos, en español
e indicando línea y columna. Todavía no ejecuta nada: eso corresponde a las
siguientes fases.

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

# Validar un programa
python src/main.py ejemplos/demo.arepa

# Ver el árbol de análisis o los tokens
python src/main.py ejemplos/demo.arepa --arbol
python src/main.py ejemplos/demo.arepa --tokens

# Correr la suite completa (8 positivos + 13 negativos + 7 de CLI)
python pruebas/test_front.py
```

La salida al validar el demo se ve así:

```text
==============================================================
 AREPA v0.1 (Fase 1 - front-end)
==============================================================
Archivo : ejemplos/demo.arepa
Análisis léxico   : OK (166 tokens)
Análisis sintáctico: OK
¡Quihubo pues! Programa bien escrito: 9 sentencia(s) reconocida(s).
```

## Qué hay en cada carpeta

| Ruta | Contenido |
|---|---|
| `gramatica/Arepa.g4` | la gramática ANTLR4 del lenguaje |
| `generado/` | lexer y parser en Python que produce ANTLR |
| `src/main.py` | interfaz de línea de comandos |
| `src/errores.py` | diagnóstico de errores en español |
| `src/arbol.py` | impresión del árbol de análisis |
| `pruebas/` | programas positivos, negativos y el corredor de pruebas |
| `ejemplos/` | demo completo y ejemplos cortos por componente |
| `docs/` | alcance, catálogo de instrucciones, gramática EBNF e informe |

## Ejemplos

* `ejemplos/demo.arepa` — flujo completo: carga, preparación, resumen, gráfica y exportación.
* `ejemplos/filtros.arepa` — carga, selección, filtros, limpieza y orden.
* `ejemplos/graficas.arepa` — los cinco tipos de gráfica con sus cláusulas.
* `ejemplos/funciones.arepa` — funciones con `invente`, condicionales y `cuenteme`.

Todos se validan con `python src/main.py ejemplos/<nombre>.arepa`.

## Documentación

* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)

## Regenerar la gramática (opcional)

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

Hace falta Java 11 y el jar `antlr-4.13.2-complete.jar`.
Otra opción es `pip install antlr4-tools` y dejar que descargue lo necesario.
En Windows también sirve el script `generar_gramatica.bat`, que busca el jar
en `%USERPROFILE%\antlr\` o toma la ruta de la variable `ANTLR_JAR`.
