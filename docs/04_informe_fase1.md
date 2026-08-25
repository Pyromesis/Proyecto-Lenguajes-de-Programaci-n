# AREPA — Informe de la Fase 1: Especificación y front-end

**Proyecto:** Lenguaje de dominio específico para ciencia de datos y visualización
**Curso:** Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2
**Fase entregada:** Corte 1 — Especificación y front-end del lenguaje

---

## 1. Qué se implementó

Se diseñó e implementó el **front-end completo** del DSL AREPA (*Análisis
Reproducible de datos Escrito con Palabras Autóctonas*), un lenguaje con
vocabulario colombiano para flujos reproducibles de datos:

1. **Especificación del lenguaje**
   - Documento de alcance: dominio, usuarios, casos de uso, entradas,
     salidas y restricciones (`docs/01_documento_alcance.md`).
   - Catálogo completo de instrucciones con justificación de cada decisión
     de diseño (`docs/02_catalogo_instrucciones.md`).
   - Gramática formal BNF/EBNF (`docs/03_gramatica_ebnf.md`).
2. **Gramática ANTLR4 combinada (lexer + parser)** en `gramatica/Arepa.g4`
   (~330 líneas documentadas): 45 palabras reservadas, 20 símbolos/operadores,
   literales enteros, decimales, cadenas con escapes, comentarios `#`,
   saltos de línea significativos e identificadores Unicode.
3. **Código generado por ANTLR4** para Python 3 en `generado/`:
   `ArepaLexer.py`, `ArepaParser.py`, `ArepaVisitor.py`, tablas `.tokens/.interp`.
   Generado con: `antlr4 -Dlanguage=Python3 -visitor -no-listener Arepa.g4`.
4. **Interfaz de línea de comandos** `src/main.py`:
   - `python src/main.py <archivo.arepa>` → valida el programa.
   - `--tokens` → vuelca la tabla de tokens (tipo, texto, línea, columna).
   - `--arbol` → imprime el árbol de análisis jerárquico.
   - Códigos de salida: `0` válido, `1` inválido, `2` archivo no encontrado.
5. **Manejo de errores** `src/errores.py`: listener propio que captura todos
   los errores sin interrumpir el análisis y traduce los mensajes técnicos de
   ANTLR a español comprensible, conservando **línea y columna**.
6. **Árbol de análisis legible** `src/arbol.py`: impresión jerárquica con
   ramas ASCII y conteo de sentencias reconocidas.
7. **Suite de pruebas léxicas y sintácticas** `pruebas/test_front.py`:
   6 programas positivos + 10 negativos = **16 pruebas, 16 pasaron**.

## 2. Alcance funcional reconocido (mínimo del corte)

| Requisito del corte | Dónde queda demostrado |
|---|---|
| Asignaciones y expresiones básicas | `pruebas/positivos/01_asignaciones_expresiones.arepa` |
| Carga de CSV con opciones | `pruebas/positivos/02_carga_y_guardado.arepa` |
| Selección de columnas y filtros sencillos | `pruebas/positivos/03_seleccion_filtro.arepa` |
| Pipelines completos con agregaciones | `pruebas/positivos/04_pipeline_completo.arepa` |
| Reconocimiento sintáctico de visualización | `pruebas/positivos/05_graficas.arepa` |
| Funciones y condicionales | `pruebas/positivos/06_funciones_condicional.arepa` |
| Programa integrador | `ejemplos/demo.arepa` |

## 3. Arquitectura de archivos

```text
proyecto/
├── gramatica/Arepa.g4        ← gramática única fuente (lexer + parser)
├── generado/                 ← código Python generado por ANTLR4
├── src/
│   ├── main.py               ← CLI: orquesta lexer/parser/reportes
│   ├── errores.py            ← listener de errores + traducción de mensajes
│   └── arbol.py              ← impresión del árbol + conteo de sentencias
├── ejemplos/demo.arepa       ← programa de referencia
├── pruebas/
│   ├── positivos/*.arepa     ← deben aceptarse
│   ├── negativos/*.arepa     ← deben rechazarse con diagnóstico
│   └── test_front.py         ← corredor de pruebas
├── docs/                     ← alcance, catálogo, EBNF e informe
├── README.md                 ← guía rápida
└── requirements.txt          ← dependencias
```

Separación lograda según lo exigido: gramática / generación / errores /
interfaz / pruebas / ejemplos / documentación.

## 4. Cómo reproducir el entorno

```bash
# 1. Python 3.11+ con el runtime de ANTLR
pip install -r requirements.txt        # antlr4-python3-runtime==4.13.2

# 2. Regenerar lexer/parser (requiere Java 11+ y antlr-4.13.2-complete.jar)
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
# Alternativa sin instalar nada global: pip install antlr4-tools && antlr4 ...

# 3. Validar un programa
python src/main.py ejemplos/demo.arepa
python src/main.py ejemplos/demo.arepa --arbol      # árbol de análisis
python src/main.py ejemplos/demo.arepa --tokens     # tabla de tokens

# 4. Suite completa de pruebas
python pruebas/test_front.py
```

## 5. Resultados de las pruebas

Ejecución de `python pruebas/test_front.py` (16/16):

| Prueba | Clase | Resultado |
|---|---|---|
| 01_asignaciones_expresiones | positiva | PASÓ |
| 02_carga_y_guardado | positiva | PASÓ |
| 03_seleccion_filtro | positiva | PASÓ |
| 04_pipeline_completo | positiva | PASÓ |
| 05_graficas | positiva | PASÓ |
| 06_funciones_condicional | positiva | PASÓ |
| n01_falta_chao | negativa | PASÓ (rechazado, L7,C0) |
| n02_cadena_sin_cerrar | negativa | PASÓ (error léxico, L2,C9) |
| n03_simbolo_raro (`@`) | negativa | PASÓ (error léxico, L4,C7) |
| n04_corchete_sin_cerrar | negativa | PASÓ (L7,C0) |
| n05_deje_sin_donde | negativa | PASÓ (L3,C14) |
| n06_asignacion_incompleta | negativa | PASÓ (L4,C3) |
| n07_fijese_sin_parentesis | negativa | PASÓ (L3,C10) |
| n08_operador_colgante | negativa | PASÓ (L2,C0) |
| n09_pinte_tipo_invalido | negativa | PASÓ (sugiere tipos válidos) |
| n10_identificador_invalido | negativa | PASÓ (L2,C0) |

Las pruebas negativas verifican además que **todo error reporte línea ≥ 1 y
columna ≥ 0**.

## 6. Problemas encontrados y cómo se resolvieron

| # | Problema | Causa raíz | Solución aplicada |
|---|---|---|---|
| P1 | Programas con comentario antes de `quihubo` fallaban | La regla inicial no admitía saltos previos | `<programa> ::= {NL} quihubo …` |
| P2 | `\|>` que abre línea no se reconocía como continuación | El pipeline solo permitía `NL` después del pipe | `( [NL] "\|>" [NL] <etapa> )*`: el pipe puede abrir o cerrar línea |
| P3 | Variable llamada `y` era imposible | `y` es palabra reservada del operador lógico | Corrección en ejemplos; decisión documentada (D5/D7): variables ≠ reservadas |
| P4 | Columna `fecha` fallaba en `[fecha, ciudad]` | `fecha` también es tipo reservado | Nueva regla `nombre_columna = ID \| cualquier_reservada`, usada en listas, ejes, renombre, conversión y átomos |
| P5 | Alias `dispersion` en `resuma` fallaba | Mismo choque palabra reservada vs. nombre externo | `item_resumen` usa `nombre_columna` |
| P6 | Cláusulas de `pinte` se interpretaban como sentencias nuevas | Ambigüedad: cualquier expresión podía iniciar sentencia | Las sentencias-expresión se restringen a llamadas (`instruccion_llamada`) y las cláusulas admiten `[NL]` antes |
| P7 | BOM UTF-8 provocaba error fantasma al inicio | PowerShell guarda UTF-8 con BOM | Lectura con `utf-8-sig` |
| P8 | Consola Windows (cp1252) rompía tildes/emojis | Codificación heredada | `sys.stdout.reconfigure(encoding="utf-8")` |

## 7. Decisiones técnicas de implementación

* **Gramática combinada** (no separada lexer/parser) para mantener una sola
  fuente coherente en Fase 1; puede dividirse en `ArepaLexer.g4`/`ArepaParser.g4` más adelante.
* **Errores sin interrupciones**: se retiran los listeners por defecto de ANTLR
  y se instala uno propio; así se reportan *todos* los problemas de una vez.
* **Traducción de mensajes**: patrones sobre los mensajes de ANTLR
  (`missing…`, `extraneous input…`, `mismatched input…`, `token recognition error…`)
  convertidos a frases en español con sugerencias (p. ej., n09 lista los tipos de gráfica válidos).
* **Salida del árbol sin ruido**: se ocultan los tokens `NL` para que la
  estructura sea legible.

## 8. Limitaciones conocidas (aceptadas en esta fase)

1. No hay ejecución semántica: `monte` aún no lee CSV ni `pinte` dibuja
   (corresponde a las fases 2 y 3).
2. No hay tabla de símbolos: usar una variable sin definir pasa el análisis
   sintáctico; se detectará con el Visitor semántico.
3. Los nombres de variables no pueden coincidir con palabras reservadas;
   sí pueden hacerlo los de columnas y alias (decisión D5).
4. Una misma línea solo contiene una sentencia; no existe separador `;`.

## 9. Plan hacia las siguientes fases

* **Fase 2:** Visitor en Python (`ArepaVisitor` ya generado), tabla de
  símbolos, ejecución real con `pandas` (monte/escoja/deje/cree/junte/resuma/guarde),
  validaciones semánticas (columnas inexistentes, tipos incompatibles,
  variables no declaradas) y pruebas unitarias/de integración.
* **Fase 3:** motor de gráficas con `matplotlib` (barras, líneas, histograma,
  dispersión, cajas), exportación PNG, mejoras de diagnóstico y caso de
  estudio completo con datos reales.

La gramática de la Fase 1 ya reconoce todo el vocabulario previsto, por lo que
las fases siguientes agregan semántica **sin romper la sintaxis**.
