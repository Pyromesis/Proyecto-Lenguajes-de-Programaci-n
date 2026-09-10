# AREPA — Matriz de trazabilidad del Primer Corte

Correspondencia verificable entre cada requisito del Corte 1 (según el PDF
de la asignatura) y su evidencia:

```text
REQUISITO → DOCUMENTACIÓN → REGLA EBNF → REGLA Arepa.g4 → CÓDIGO → PRUEBA → EJEMPLO
```

Convenciones: "EBNF" remite a `docs/03_gramatica_ebnf.md`; "ANTLR" remite a
`gramatica/Arepa.g4` con su línea; "Prueba" remite a `pruebas/`. Todas las
filas tienen estado **VERIFICADO** con la ejecución de
`python3 pruebas/test_proyecto.py` (194 → ver conteo vigente en §8 de
`docs/05_arquitectura.md` y en README).

| ID | Requisito | Documento | Regla EBNF | Regla ANTLR (línea) | Código | Prueba | Ejemplo | Estado |
|----|-----------|-----------|------------|---------------------|--------|--------|---------|--------|
| R01 | Delimitación del dominio y casos de uso | `docs/01` §1 y §3 | — | — | — | — | `ejemplos/demo.arepa` (flujo completo) | VERIFICADO |
| R02 | Usuarios | `docs/01` §2 | — | — | — | — | — | VERIFICADO |
| R03 | Entradas | `docs/01` §4 | — | — | — | — | `datos/*.csv`, `*.arepa` | VERIFICADO |
| R04 | Salidas | `docs/01` §5 | — | — | `src/cli/main.py` | `test_front.py` (CLI) | salida del demo | VERIFICADO |
| R05 | Restricciones | `docs/01` §6 | EBNF §1-§2 | `programa` (38) | `src/lenguaje/analizador.py` | `n01`, `n12`, `n14` | — | VERIFICADO |
| R06 | Palabras reservadas | `docs/02` §1 y §3 | EBNF §6 `PALABRA_RESERVADA` (59) | líneas 329-414 | `generado/ArepaLexer.py` | `test_front.py` (positivos) + `n11` | `docs/02` §3 (tabla) | VERIFICADO |
| R07 | Operadores | `docs/02` §4 | EBNF §6 (tabla de símbolos) | líneas 384-400 | `src/expresiones/operadores.py` | `test_expresiones.py` (16) | `01_asignaciones_expresiones.arepa` | VERIFICADO |
| R08 | Literales (enteros, decimales, cadenas, lógicos, nada) | `docs/02` §5 | EBNF §6 (`ENTERO`, `DECIMAL`, `CADENA`, `ESCAPE`) | `DECIMAL` (418), `ENTERO` (419), `CADENA` (420), `OBVIO/FALSO/NADA` (406-408) | `src/datos/tipos.py`, `src/expresiones/evaluador.py` | `test_expresiones.py`, `test_datos.py::tipos_*` | `08_casos_borde.arepa` (escapes, `""`) | VERIFICADO |
| R09 | Sentencias | `docs/02` §2-§3 | EBNF §2 `<sentencia>` | `sentencia` (48) | `src/runtime/ejecutor.py` | `test_front.py` (positivos) | `ejemplos/demo.arepa` (9 sentencias) | VERIFICADO |
| R10 | Gramática BNF/EBNF | `docs/03` completo | — | — | — | chequeo automático 46/46 reglas | — | VERIFICADO |
| R11 | Gramática implementada en ANTLR4 | `docs/04` §1.2, README | — | `grammar Arepa;` (25) | `gramatica/Arepa.g4` | regeneración con `generar_gramatica.sh` + re-test | — | VERIFICADO |
| R12 | Lexer y parser para Python | README (Dependencias) | — | — | `generado/ArepaLexer.py`, `generado/ArepaParser.py` | `test_front.py` (todo pasa tras regenerar) | — | VERIFICADO |
| R13 | Validación de programas correctos | `docs/01` §7 | — | — | `src/lenguaje/analizador.py::analizar` | `test_front.py` 8 positivos | `pruebas/positivos/*.arepa` | VERIFICADO |
| R14 | Validación de programas incorrectos | `docs/04` §5 | — | — | `src/lenguaje/errores.py::syntaxError` (32) | `test_front.py` 20 negativos | `pruebas/negativos/*.arepa` | VERIFICADO |
| R15 | Asignaciones y expresiones básicas | `docs/02` §3.5, §4 | EBNF §2-§3 (`<asignacion>`, `<expresion>`) | `asignacion` (72), `expresion` (144), `expresion_logica` (233) | `src/expresiones/evaluador.py`, `runtime/ejecutor.py::visitAsignacion` (143) | `test_arbol.py::arbol_de_asignacion`, `test_expresiones.py` | `01_asignaciones_expresiones.arepa` | VERIFICADO |
| R16 | Reconocimiento de carga CSV | `docs/02` §3.1 | EBNF §4 (`<instruccion_monte>`) | `instruccion_monte` (168), `MONTE` (334) | `runtime/ejecutor.py::_cargar` (193), `datos/lector_csv.py` | `test_runtime.py::monte_carga_csv_real`, `test_datos.py` (csv_*), `n17` | `demo.arepa` (monte con separador) | VERIFICADO |
| R17 | Selección de columnas | `docs/02` §3.2 | EBNF §4 (`escoja <lista_columnas>`) | `operacion_datos` (155), `ESCOJA` (343) | `runtime/ejecutor.py::_aplicar_operacion`, `datos/tabla.py::seleccionar` | `test_arbol.py::arbol_de_seleccion`, `test_runtime.py::escoja_selecciona_columnas`, `n04`, `n16` | `03_seleccion_filtro.arepa` | VERIFICADO |
| R18 | Filtros con comparaciones sencillas | `docs/02` §3.2 | EBNF §4 (`deje donde`) + `<operador_relacional>` | `DEJE` (344), `DONDE` (345), `operador_relacional` (250) | `runtime/ejecutor.py` (rama DEJE), `datos/tabla.py::filtrar` | `test_arbol.py::arbol_de_filtro`, `test_runtime.py::deje_donde_filtra_filas`, `n05` | `03_seleccion_filtro.arepa` (los 6 relacionales) | VERIFICADO |
| R19 | Visualización reconocida sintácticamente (sin gráfica) | `docs/02` §3.4 | EBNF §5 (`<instruccion_grafica>`) | `instruccion_grafica` (205), `PINTE` (371) | `runtime/ejecutor.py::visitInstruccion_grafica` (433) | `test_arbol.py::arbol_de_visualizacion`, `n09`, `n13` | `05_graficas.arepa`, `ejemplos/graficas.arepa` | VERIFICADO |
| R20 | Documento de alcance | `docs/01` completo | — | — | — | — | — | VERIFICADO |
| R21 | Catálogo de instrucciones | `docs/02` completo | — | — | — | — | — | VERIFICADO |
| R22 | Archivo `.g4` | README (Gramática) | — | `gramatica/Arepa.g4` | — | `test_proyecto.py` completo | — | VERIFICADO |
| R23 | Código generado por ANTLR | README (Estructura) | — | — | `generado/` (Lexer, Parser, Visitor, `.tokens`) | sincronía 46/46 reglas | — | VERIFICADO |
| R24 | Pruebas léxicas y sintácticas | `docs/04` §5 | — | — | `pruebas/` (6 suites) | `python3 pruebas/test_proyecto.py` | — | VERIFICADO |
| R25 | Ejemplos | README (Ejemplos) | — | — | — | validación de los 5 con la CLI | `ejemplos/` | VERIFICADO |
| R26 | README | `README.md` completo | — | — | — | comandos ejecutados uno a uno | — | VERIFICADO |
| R27 | Árbol de análisis | README (Árbol), `docs/06` §4 | — | — | `src/lenguaje/arbol.py::imprimir_arbol` (46) | `test_arbol.py` (21) + CLI `--arbol` | salida real en README | VERIFICADO |
| R28 | Errores comprensibles (línea y columna) | `docs/04` §5 y §7 | — | — | `src/lenguaje/errores.py::_traducir` (153), `src/errores_base.py` | `test_front.py` (10 de diagnóstico) | mensajes reales en README (Errores) | VERIFICADO |
| R29 | Comentarios | `docs/02` §2 | EBNF §6 (`COMENTARIO`) | `COMENTARIO` (451) | `generado/ArepaLexer.py` (skip) | `test_front.py::probar_diagnosticos` caso 8 | `08_casos_borde.arepa` (en 3 posiciones) | VERIFICADO |
| R30 | Identificadores (Unicode, ñ, tildes) | `docs/02` §1.1, `docs/03` §6 | EBNF §6 (`<identificador>`) | `ID` (455) | `runtime/simbolos.py::validar_identificador` | `test_simbolos.py::identificador_*`, `n10` | `08_casos_borde.arepa` (`valor_año`, `piña_dulce`) | VERIFICADO |
| R31 | Colisiones reservada/identificador/columna | `docs/02` §1.1 (D5) | EBNF §3 (`<nombre_columna>`) | `nombre_columna` (310-321) | `expresiones/evaluador.py::_resolver_nombre` | `n11`, `test_front.py` diagnóstico caso 4 | `numerito`, `y2` en `08_casos_borde.arepa` | VERIFICADO |
| R32 | Precedencia y asociatividad | `docs/02` §4 | EBNF §3 (jerarquía de expresiones) | `expresion_logica` (233) → `factor` | `expresiones/evaluador.py` | `test_arbol.py` (10 casos de precedencia) | `08_casos_borde.arepa` (`2 ^ 3 ^ 2`) | VERIFICADO |
| R33 | Pipeline `|>` | `docs/02` §6 (D3) | EBNF §3 (`<expresion>`) | `PIPE` (424), `expresion` (144) | `runtime/ejecutor.py::visitExpresion` (152) | `test_arbol.py::arbol_de_pipeline_con_etapas` | `demo.arepa` | VERIFICADO |
| R34 | Condicionales y funciones (sintaxis declarada) | `docs/02` §3.5 (D7) | EBNF §2 | `condicional` (106), `definicion_funcion` (95) | `runtime/ejecutor.py` | `test_runtime.py::invente_devuelva_y_recursion`, `n07` | `06_funciones_condicional.arepa` | VERIFICADO |

Notas de decisiones intencionales (no son contradicciones):

* `nombre_columna` acepta cualquier palabra reservada (R31, decisión D5):
  los nombres de columnas vienen de CSV externos. Consecuencia documentada:
  `v = monte` o `r = t |> escoja` solos son sintácticamente válidos (la
  reservada queda como referencia de columna); por eso las negativas de
  carga/selección incompleta usan formas realmente inválidas (`monte 42`,
  `escoja []`).
* `pinte` se reconoce y valida pero no produce imágenes (R19): el PDF
  establece que en este corte la visualización es solo sintáctica.
