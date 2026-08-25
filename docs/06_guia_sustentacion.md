# AREPA — Guía de sustentación (Corte 1)

Ruta rápida para demostrar en vivo cada punto del primer corte. Para cada
punto: dónde está el código, qué prueba lo respalda y qué ejemplo mostrar.

Comandos base (desde la raíz del proyecto):

```bash
pip install -r requirements.txt
python src/cli/main.py ejemplos/demo.arepa --arbol
python pruebas/test_proyecto.py
```

---

## 1. Dónde está la gramática

* **Archivo:** `gramatica/Arepa.g4` (fuente única, gramática combinada).
  Reglas principales: `programa` (línea 38), `sentencia` (48),
  `asignacion` (68), `operacion_datos` (127), `instruccion_monte` (140),
  `instruccion_grafica` (177), `expresion_logica` (205).
* **Especificación equivalente:** `docs/03_gramatica_ebnf.md`.
* **Prueba:** las 150 de `python pruebas/test_proyecto.py` parsean con
  esta gramática.
* **Ejemplo en vivo:** abrir `Arepa.g4` y mostrar `programa` y
  `instruccion_grafica`.

## 2. Cómo se genera el lexer/parser

* **Procedimiento:** `antlr4 -Dlanguage=Python3 -visitor -no-listener -o
  generado gramatica/Arepa.g4` o `generar_gramatica.bat` en Windows.
* **Archivos generados:** `generado/ArepaLexer.py`, `ArepaParser.py`,
  `ArepaVisitor.py` (encabezado "Generated from gramatica/Arepa.g4 by
  ANTLR 4.13.2"; nunca se editan a mano).
* **Versión documentada:** runtime `antlr4-python3-runtime==4.13.2` en
  `requirements.txt`, misma del jar.
* **Demostración:** ejecutar `generar_gramatica.bat` y volver a correr
  `python pruebas/test_proyecto.py` sin que cambie el resultado.

## 3. Cómo se reconoce un programa

* **Archivo:** `src/lenguaje/analizador.py`, función `analizar` (línea 30):
  crea lexer y parser de ANTLR, les instala el listener propio y devuelve
  `(parser, arbol, errores)`.
* **Gramática:** regla inicial `programa : NL* QUIHUBO NL+ sentencias?
  NL* CHAO NL* EOF`.
* **Prueba:** `test_front.py` — 8 positivos aceptados, 14 negativos
  rechazados.
* **Ejemplo:** `python src/cli/main.py ejemplos/demo.arepa` → "Programa
  bien escrito: 9 sentencia(s) reconocida(s)".

## 4. Cómo se genera el árbol

* **Archivo:** `src/lenguaje/arbol.py`, `imprimir_arbol` (línea 46):
  recorrido propio con ramas ASCII, oculta los saltos de línea.
* **Comando:** `python src/cli/main.py ejemplos/demo.arepa --arbol`.
* **Prueba:** `test_arbol.py` (15 casos) recorre el árbol
  programáticamente y verifica jerarquía y precedencia.
* **Ejemplo:** mostrar en pantalla el subárbol de `asignacion` del demo.

## 5. Cómo se detecta un programa inválido

* **Archivo:** `src/lenguaje/errores.py`, `syntaxError` (línea 32) captura
  todo sin detener el análisis; `_traducir` (línea 145) pasa el mensaje
  técnico a español.
* **Gramática:** cualquier desviación produce error del listener; el
  programa nunca se cae con excepciones no controladas (verificado con 10
  entradas malformadas).
* **Prueba:** `test_front.py` — 14 negativos + 7 de diagnóstico.
* **Ejemplo:** `python src/cli/main.py pruebas/negativos/n01_falta_chao.arepa`
  → rechazado con línea y columna.

## 6. Cómo se reporta línea y columna

* **Archivo:** `src/lenguaje/errores.py` (conserva `linea` y `columna` de
  ANTLR) y `src/cli/main.py` (las imprime con el formato "Línea X, Columna
  Y").
* **Prueba:** `test_front.py::probar_diagnosticos` — caso 1 verifica
  línea 2 columna 6 exactas para un `@`; caso 2 verifica que un error de
  la línea 4 se reporte en la línea 4; los 14 negativos validan posición.
* **Ejemplo:** `x = 1 @ 2` → `[léxico] Línea 2, Columna 6: Hay un símbolo
  '@' que no hace parte del lenguaje AREPA`.

## 7. Cómo se implementan asignaciones y expresiones

* **Gramática:** `asignacion` (Arepa.g4:68) y la jerarquía
  `expresion_logica → conjuncion → negacion → comparacion → aritmetica →
  termino → factor → unario → atomo`, que codifica la precedencia
  documentada (`o < y < no < comparación < +- < */% < ^ derecha < - unario`).
* **Código propio:** `src/expresiones/evaluador.py` (`evaluar` línea 71,
  `visitAritmetica` 126) y `src/expresiones/operadores.py`; en el runtime,
  `src/runtime/ejecutor.py::visitAsignacion` (línea 110).
* **Prueba:** `test_arbol.py` (precedencia en la forma del árbol),
  `test_expresiones.py` (14 casos: `1 + 2 * 3 == 7`, `2 ^ 3 ^ 2 == 512`,
  `(1 + 2) * 3`, errores de tipos).
* **Ejemplo:** `pruebas/positivos/01_asignaciones_expresiones.arepa`.

## 8. Cómo se reconoce CSV

* **Gramática:** `instruccion_monte` (Arepa.g4:140): `monte cadena
  opciones_archivo?` con opciones `encabezado` y `separador`.
* **Código propio:** `src/runtime/ejecutor.py::_cargar` (línea 160) usa el
  lector propio `src/datos/lector_csv.py` (máquina de estados con comillas
  y escape `""`).
* **Prueba:** `test_runtime.py::monte_carga_csv_real` y los 12 casos
  `csv_*` de `test_datos.py`.
* **Ejemplo:** `ejemplos/demo.arepa` línea `ventas = monte
  "datos/ventas.csv" con encabezado, separador ","`.

## 9. Cómo se reconoce selección

* **Gramática:** alternativa `ESCOJA lista_columnas` dentro de
  `operacion_datos` (Arepa.g4:127).
* **Código propio:** `src/runtime/ejecutor.py::_aplicar_operacion`
  (línea 179, rama ESCOJA) sobre `Tabla.seleccionar`
  (`src/datos/tabla.py`).
* **Prueba:** `test_arbol.py::arbol_de_seleccion` (estructura) y
  `test_runtime.py::escoja_selecciona_columnas`.
* **Ejemplo:** `pruebas/positivos/03_seleccion_filtro.arepa`.

## 10. Cómo se reconoce filtro

* **Gramática:** alternativa `DEJE DONDE expresion_logica` en
  `operacion_datos`.
* **Código propio:** misma rama de `_aplicar_operacion`; la condición se
  evalúa fila a fila con el evaluador propio.
* **Prueba:** `test_arbol.py::arbol_de_filtro`,
  `test_runtime.py::deje_donde_filtra_filas`; negativa
  `n05_deje_sin_donde`.
* **Ejemplo:** `|> deje donde unidades > 0 y precio > 0` (demo).

## 11. Cómo se reconoce visualización (solo sintáctico)

* **Gramática:** `instruccion_grafica` (Arepa.g4:177): `pinte
  tipo_grafica identificador (clausula_estetica)* (final_grafica)?` con
  tipos `barras|lineas|histograma|dispersion|cajas`.
* **Código propio:** `src/runtime/ejecutor.py::visitInstruccion_grafica`
  (línea 396): valida que la tabla exista y que las columnas de
  `ejex`/`ejey` existan; avisa que la imagen llega en la Fase 3.
* **Prueba:** `test_arbol.py::arbol_de_visualizacion` (estructura con
  cláusulas y cierre), negativas `n09_pinte_tipo_invalido` y
  `n13_pinte_sin_tabla`, semántica `pinte_valida_columnas_de_la_grafica`.
* **Ejemplo:** `ejemplos/graficas.arepa` (las cinco formas).

---

## Evidencia transversal

* **Matriz requisito → prueba → resultado:** `docs/05_arquitectura.md`, §8.
* **Trazabilidad funcionalidad → archivo → función → prueba:**
  `docs/05_arquitectura.md`, §10.
* **Cadena completa requisito → documento → gramática → código → prueba →
  ejemplo:** `docs/01` (requisitos), `docs/02` (diseño), `docs/03` (EBNF),
  `gramatica/Arepa.g4`, `src/`, `pruebas/`, `ejemplos/`.
