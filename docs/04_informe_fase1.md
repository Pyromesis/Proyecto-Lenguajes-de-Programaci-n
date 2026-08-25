# AREPA — Informe de la Fase 1: Especificación y front-end

**Proyecto:** Lenguaje de dominio específico para ciencia de datos y visualización
**Curso:** Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2
**Fase entregada:** Corte 1 — Especificación y front-end del lenguaje

---

## 1. Qué se implementó

En este primer corte quedo listo el **front-end completo** del DSL AREPA
(*Análisis Reproducible de datos Escrito con Palabras Autóctonas*), el
lenguaje con vocabulario colombiano para flujos de datos reproducibles:

1. **Especificación del lenguaje**
   - Documento de alcance con dominio, usuarios, casos de uso, entradas,
     salidas y restricciones (`docs/01_documento_alcance.md`).
   - Catálogo de instrucciones con la justificación de cada decisión de
     diseño (`docs/02_catalogo_instrucciones.md`).
   - Gramática formal en BNF/EBNF (`docs/03_gramatica_ebnf.md`).
2. **Gramática ANTLR4 combinada (lexer + parser)** en `gramatica/Arepa.g4`
   (~330 líneas de código, 410 con comentarios y blancos): 51 palabras
   reservadas (45 instrucciones y estructuras, 3 literales especiales y 3
   operadores lógicos), 22 símbolos y operadores, literales enteros y
   decimales, cadenas con escapes, comentarios con `#`, saltos de línea
   significativos e identificadores Unicode.
3. **Código generado por ANTLR4** para Python 3 en `generado/`:
   `ArepaLexer.py`, `ArepaParser.py`, `ArepaVisitor.py` y las tablas
   `.tokens/.interp`. Se generó con
   `antlr4 -Dlanguage=Python3 -visitor -no-listener Arepa.g4`.
4. **Interfaz de línea de comandos** `src/cli/main.py`:
   - `python src/cli/main.py <archivo.arepa>` valida el programa.
   - `--tokens` muestra la tabla de tokens (tipo, texto, línea, columna).
   - `--arbol` imprime el árbol de análisis jerárquico.
   - `--ejecutar` corre el programa con la biblioteca propia del equipo.
   - Códigos de salida: `0` válido, `1` inválido, `2` archivo no encontrado.
5. **Manejo de errores** `src/lenguaje/errores.py`: un listener propio que atrapa
   todos los errores sin detener el análisis y pasa los mensajes técnicos de
   ANTLR a español, conservando **línea y columna**. Los conjuntos de tokens
   esperados se traducen y se limitan a 6 opciones ("entre otras opciones"),
   y si se usa una palabra reservada como variable el mensaje lo explica.
   Los errores semánticos y de ejecución usan la jerarquía propia de
   `src/errores_base.py`.
6. **Árbol de análisis legible** `src/lenguaje/arbol.py`: impresión jerárquica con
   ramas ASCII y conteo de sentencias reconocidas.
7. **Biblioteca propia del lenguaje** (implementada desde cero, ver
   `docs/05_arquitectura.md`): `src/datos/` (Tabla, Columna, Fila, lector
   y escritor CSV, tipos), `src/expresiones/` (operadores y evaluador) y
   `src/runtime/` (símbolos, contexto y ejecutor). Sin pandas, NumPy ni
   bibliotecas equivalentes.
8. **Suite de pruebas** `pruebas/test_proyecto.py`: 6 suites con 161
   pruebas en total (43 de front-end, 19 de estructura del árbol, 42 de
   datos, 14 de expresiones, 15 de símbolos y contexto, y 28 de
   runtime); todas pasan.

## 2. Alcance funcional reconocido (mínimo del corte)

| Requisito del corte | Dónde queda demostrado |
|---|---|
| Asignaciones y expresiones básicas | `pruebas/positivos/01_asignaciones_expresiones.arepa` |
| Carga de CSV con opciones | `pruebas/positivos/02_carga_y_guardado.arepa` |
| Selección de columnas y filtros sencillos | `pruebas/positivos/03_seleccion_filtro.arepa` |
| Pipelines completos con agregaciones | `pruebas/positivos/04_pipeline_completo.arepa` |
| Reconocimiento sintáctico de visualización | `pruebas/positivos/05_graficas.arepa` |
| Funciones y condicionales | `pruebas/positivos/06_funciones_condicional.arepa` |
| Preparación completa (renombre, limpie, convierta, acomode) | `pruebas/positivos/07_preparacion_completa.arepa` |
| Casos borde (escapes, unarios, continuación, bloques vacíos) | `pruebas/positivos/08_casos_borde.arepa` |
| Programa integrador | `ejemplos/demo.arepa` |
| Ejemplos por componente | `ejemplos/filtros.arepa`, `ejemplos/graficas.arepa`, `ejemplos/funciones.arepa` |

## 3. Organización de los archivos

```text
proyecto/
├── gramatica/Arepa.g4        gramática única fuente (lexer + parser)
├── generado/                 código Python generado por ANTLR4
├── src/
│   ├── lenguaje/             front-end: analizador, árbol y diagnóstico
│   ├── datos/                propia: Tabla, Columna, Fila, CSV, tipos
│   ├── expresiones/          propia: operadores y evaluador
│   ├── runtime/              propia: símbolos, contexto y ejecutor
│   ├── errores_base.py       jerarquía propia de errores
│   └── cli/main.py           CLI: valida y (--ejecutar) corre programas
├── datos/                    CSV de ejemplo para los programas
├── ejemplos/                 demo + ejemplos por componente
│   ├── demo.arepa            programa de referencia (flujo completo)
│   ├── filtros.arepa         carga, selección, filtros y preparación
│   ├── graficas.arepa        los cinco tipos de gráfica
│   └── funciones.arepa       invente, fijese_si/sino y cuenteme
├── pruebas/
│   ├── positivos/*.arepa     deben aceptarse
│   ├── negativos/*.arepa     deben rechazarse con diagnóstico
│   ├── test_front.py         suite del front-end (43: 8 pos + 17 neg + 10 diag + 8 CLI)
│   ├── test_arbol.py         suite de estructura del árbol (19)
│   ├── test_datos.py         suite de la biblioteca de datos (42)
│   ├── test_expresiones.py   suite del evaluador (14)
│   ├── test_simbolos.py      suite de símbolos y contexto (15)
│   ├── test_runtime.py       suite del runtime (28)
│   └── test_proyecto.py      corredor maestro (161)
├── docs/                     alcance, catálogo, EBNF, informe y arquitectura
├── README.md                 guía rápida
└── requirements.txt          dependencias (solo ANTLR4)
```

Con esta organización se cumplió la separación pedida: gramática /
generación / lenguaje / datos / expresiones / runtime / interfaz /
pruebas / ejemplos / documentación.

## 4. Cómo reproducir el entorno

```bash
# 1. Python 3.11+ con el runtime de ANTLR
pip install -r requirements.txt        # antlr4-python3-runtime==4.13.2

# 2. Regenerar lexer/parser (requiere Java 11+ y antlr-4.13.2-complete.jar)
antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
# Alternativa sin instalar nada global: pip install antlr4-tools && antlr4 ...
# En Windows también sirve el script generar_gramatica.bat (busca el jar
# en %USERPROFILE%\antlr o usa la variable ANTLR_JAR).

# 3. Validar un programa
python src/cli/main.py ejemplos/demo.arepa
python src/cli/main.py ejemplos/demo.arepa --arbol      # árbol de análisis
python src/cli/main.py ejemplos/demo.arepa --tokens     # tabla de tokens
python src/cli/main.py ejemplos/demo.arepa --ejecutar   # corre con la biblioteca propia

# 4. Suite completa de pruebas (161)
python pruebas/test_proyecto.py
```

## 5. Resultados de las pruebas

Ejecutando `python pruebas/test_front.py` pasan las 43 pruebas
(8 positivas + 17 negativas + 10 de diagnóstico + 8 de la interfaz):

| Prueba | Clase | Resultado |
|---|---|---|
| 01_asignaciones_expresiones | positiva | PASÓ |
| 02_carga_y_guardado | positiva | PASÓ |
| 03_seleccion_filtro | positiva | PASÓ |
| 04_pipeline_completo | positiva | PASÓ |
| 05_graficas | positiva | PASÓ |
| 06_funciones_condicional | positiva | PASÓ |
| 07_preparacion_completa | positiva | PASÓ |
| 08_casos_borde | positiva | PASÓ |
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
| n11_reservada_como_variable | negativa | PASÓ (L3,C0, explica que `y` es reservada) |
| n12_quihubo_chao_misma_linea | negativa | PASÓ (L2,C8) |
| n13_pinte_sin_tabla | negativa | PASÓ (L4,C12) |
| n14_chao_incorrecto | negativa | PASÓ (L5,C5, 'chaoo' no es el cierre) |
| n15_sin_quihubo | negativa | PASÓ (L2,C0, sin apertura) |
| n16_seleccion_incompleta | negativa | PASÓ (L4,C17, lista vacía) |
| n17_monte_sin_cadena | negativa | PASÓ (L3,C10, falta la ruta) |
| Diagnóstico: léxico con línea/columna exactas | diagnóstico | PASÓ |
| Diagnóstico: error de la línea 4 reportado en la línea 4 | diagnóstico | PASÓ |
| Diagnóstico: cadena sin cerrar en español | diagnóstico | PASÓ |
| Diagnóstico: reservada como variable con pista | diagnóstico | PASÓ |
| Diagnóstico: delimitador faltante señala el '(' | diagnóstico | PASÓ |
| Diagnóstico: 'chao' con contenido extra se rechaza | diagnóstico | PASÓ |
| Diagnóstico: 10 entradas malformadas sin excepciones | diagnóstico | PASÓ |
| CLI: código 0 en programa válido | interfaz | PASÓ |
| CLI: mensaje de programa bien escrito | interfaz | PASÓ |
| CLI: `--arbol` imprime el árbol | interfaz | PASÓ |
| CLI: `--tokens` imprime la tabla | interfaz | PASÓ |
| CLI: código 1 en programa inválido | interfaz | PASÓ |
| CLI: reporta la línea del error | interfaz | PASÓ |
| CLI: código 2 con archivo inexistente | interfaz | PASÓ |

Las negativas comprueban además que **todo error reporte línea mayor o igual
a 1 y columna mayor o igual a 0**, que ningún mensaje contenga saltos de
línea crudos y que ninguno sea un volcado de más de 300 caracteres.

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
| P8 | Consola Windows (cp1252) rompía tildes y caracteres especiales | Codificación heredada del sistema | `sys.stdout.reconfigure(encoding="utf-8")` en `main.py` y en el corredor de pruebas |
| P9 | `quihubo chao` en una misma línea se aceptaba | La regla `programa` permitía cero saltos tras la apertura | `NL+` obligatorio después de `quihubo`; cubierto por la negativa n12 |
| P10 | Mensajes como `Esa construcción '\\ny' no cuadra…` confundían | ANTLR incluye saltos crudos y conjuntos de 50+ tokens en sus mensajes | Traducción de tokens, límite de 6 opciones por conjunto y pista cuando se usa una reservada como variable |

## 7. Decisiones técnicas de implementación

* **Gramática combinada** (no separada en lexer/parser) para conservar una
  sola fuente coherente en la Fase 1; más adelante puede dividirse en
  `ArepaLexer.g4` y `ArepaParser.g4` si hace falta.
* **Errores sin interrupciones**: se retiran los listeners por defecto de
  ANTLR y se instala uno propio, de modo que se reportan *todos* los
  problemas de una sola pasada.
* **Traducción de mensajes**: patrones sobre los mensajes de ANTLR
  (`missing…`, `extraneous input…`, `mismatched input…`, `token recognition error…`)
  convertidos a frases en español con sugerencias: los nombres simbólicos se
  traducen (`NL` es "un salto de línea", `ID` es "un identificador"), los
  conjuntos esperados se limitan a 6 opciones y, si el error viene de usar
  `y`, `o`, `no`, `obvio`, `falso` o `nada` como variable, el mensaje lo
  explica (p. ej., n09 lista los tipos de gráfica válidos y n11 la pista de
  palabra reservada).
* **Salida del árbol sin ruido**: los tokens `NL` se ocultan para que la
  estructura se pueda leer.

## 8. Limitaciones conocidas (aceptadas en esta fase)

1. No hay ejecución semántica: `monte` todavía no lee CSV ni `pinte` dibuja
   (eso va para las fases 2 y 3).
2. No hay tabla de símbolos: usar una variable sin definir pasa el análisis
   sintáctico; se detectará con el Visitor semántico.
3. Los nombres de variables no pueden coincidir con palabras reservadas;
   sí pueden hacerlo los de columnas y alias (decisión D5).
4. Una línea contiene una sola sentencia; no existe separador `;`.
5. Por la decisión D5, una expresión puede contener cualquier reservada en
   posición de columna, de modo que un typo como `x = unidades * pinte` pasa
   el análisis sin aviso (la columna podría existir realmente). Detectar
   esos casos exige la tabla de símbolos de la Fase 2, que validará contra
   las columnas reales del CSV.

## 9. Plan hacia las siguientes fases

* **Fase 2:** consolidar la semántica sobre la biblioteca propia ya
  construida: tabla de símbolos con validaciones más finas (columnas
  inexistentes en tiempo de análisis, tipos incompatibles, variables no
  declaradas), más pruebas de integración y mensajes aún más claros.
  Todo sobre `Tabla`, el lector CSV propio y el evaluador propio; sin
  pandas ni bibliotecas externas.
* **Fase 3:** motor de gráficas **propio** (barras, líneas, histograma,
  dispersión, cajas) que genere imágenes sin matplotlib, exportación
  PNG y un caso de estudio completo con datos reales.

Como la gramática de la Fase 1 ya reconoce todo el vocabulario previsto,
las fases siguientes agregan la semántica **sin tener que tocar la sintaxis**.
