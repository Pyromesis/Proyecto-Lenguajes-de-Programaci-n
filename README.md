# AREPA 🫓

**A**nálisis **R**eproducible de datos **E**scrito con **P**alabras
**A**utóctonas — un DSL con vocabulario colombiano para ciencia de datos y
visualización.

Proyecto de la materia *Lenguajes de Programación y Transducción*
(Universidad Sergio Arboleda, 2026-2). Construido con **ANTLR4 + Python**.

> Estado: **Fase 1 — Especificación y front-end** ✅
> El sistema reconoce programas `.arepa`, genera el árbol de análisis y
> reporta errores léxicos/sintácticos en español, con línea y columna.

## Ejemplo

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

## Uso rápido

```bash
pip install -r requirements.txt

# Validar un programa
python src/main.py ejemplos/demo.arepa

# Ver el árbol de análisis o los tokens
python src/main.py ejemplos/demo.arepa --arbol
python src/main.py ejemplos/demo.arepa --tokens

# Suite de pruebas (16 casos positivos + negativos)
python pruebas/test_front.py
```

Salida esperada:

```text
==============================================================
 AREPA v0.1 (Fase 1 - front-end)
==============================================================
Archivo : ejemplos/demo.arepa
Análisis léxico   : OK (166 tokens)
Análisis sintáctico: OK
¡Quihubo pues! Programa bien escrito: 9 sentencia(s) reconocida(s).
```

## Estructura

| Ruta | Contenido |
|---|---|
| `gramatica/Arepa.g4` | gramática ANTLR4 del lenguaje |
| `generado/` | lexer/parser Python generados |
| `src/main.py` | interfaz de línea de comandos |
| `src/errores.py` | diagnóstico de errores en español |
| `src/arbol.py` | impresión del árbol de análisis |
| `pruebas/` | programas positivos, negativos y corredor de pruebas |
| `ejemplos/` | programa demo |
| `docs/` | alcance, catálogo de instrucciones, gramática EBNF e informe |

## Documentación

* [Documento de alcance](docs/01_documento_alcance.md)
* [Catálogo de instrucciones y decisiones de diseño](docs/02_catalogo_instrucciones.md)
* [Gramática BNF/EBNF](docs/03_gramatica_ebnf.md)
* [Informe de la Fase 1](docs/04_informe_fase1.md)

## Regenerar la gramática (opcional)

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
```

Requiere Java 11+ y el jar `antlr-4.13.2-complete.jar`
(o `pip install antlr4-tools` para automatizarlo).
