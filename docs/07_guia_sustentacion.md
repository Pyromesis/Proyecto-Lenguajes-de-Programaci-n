# AREPA — Guía de sustentación (Cortes 1 a 3)

Ruta rápida para demostrar en vivo cada punto de los tres cortes. Para cada
punto: dónde está el código, qué prueba lo respalda y qué ejemplo mostrar.

Comandos base (desde la raíz del proyecto, en una terminal Linux):

```bash
python3 --version
java -version
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
./generar_gramatica.sh
python3 src/cli/main.py ejemplos/demo.arepa
python3 src/cli/main.py ejemplos/demo.arepa --tokens
python3 src/cli/main.py ejemplos/demo.arepa --arbol
python3 pruebas/test_proyecto.py
```

---

## 1. Dónde está la gramática

* **Archivo:** `gramatica/Arepa.g4` (fuente única, gramática combinada).
  Reglas principales: `programa` (línea 38), `sentencia` (48),
  `asignacion` (75), `operacion_datos` (174), `instruccion_monte` (187),
  `instruccion_grafica` (224), `expresion_logica` (252).
* **Especificación equivalente:** `docs/03_gramatica_ebnf.md`.
* **Prueba:** las 319 de `python3 pruebas/test_proyecto.py` parsean con
  esta gramática.
* **Ejemplo en vivo:** abrir `Arepa.g4` y mostrar `programa` y
  `instruccion_grafica`.

## 2. Cómo se genera el lexer/parser

* **Procedimiento:** `antlr4 -Dlanguage=Python3 -visitor -no-listener -o
  generado gramatica/Arepa.g4` o `./generar_gramatica.sh`.
* **Archivos generados:** `generado/ArepaLexer.py`, `ArepaParser.py`,
  `ArepaVisitor.py` (encabezado "Generated from gramatica/Arepa.g4 by
  ANTLR 4.13.2"; nunca se editan a mano).
* **Versión documentada:** runtime `antlr4-python3-runtime==4.13.2` en
  `requirements.txt`, misma del jar.
* **Demostración:** ejecutar `./generar_gramatica.sh` y volver a correr
  `python3 pruebas/test_proyecto.py` sin que cambie el resultado.

## 3. Cómo se reconoce un programa

* **Archivo:** `src/lenguaje/analizador.py`, función `analizar` (línea 30):
  crea lexer y parser de ANTLR, les instala el listener propio y devuelve
  `(parser, arbol, errores)`.
* **Gramática:** regla inicial `programa : NL* QUIHUBO NL+ sentencias?
  NL* CHAO NL* EOF`.
* **Prueba:** `test_front.py` — 10 positivos aceptados, 22 negativos
  rechazados.
* **Ejemplo:** `python3 src/cli/main.py ejemplos/demo.arepa` → "Programa
  bien escrito: 9 sentencia(s) reconocida(s)".

## 4. Cómo se genera el árbol

* **Archivo:** `src/lenguaje/arbol.py`, `imprimir_arbol` (línea 46):
  recorrido propio con ramas ASCII, oculta los saltos de línea.
* **Comando:** `python3 src/cli/main.py ejemplos/demo.arepa --arbol`.
* **Prueba:** `test_arbol.py` (28 casos) recorre el árbol
  programáticamente y verifica jerarquía y precedencia.
* **Ejemplo:** mostrar en pantalla el subárbol de `asignacion` del demo.

## 5. Cómo se detecta un programa inválido

* **Archivo:** `src/lenguaje/errores.py`, `syntaxError` (línea 32) captura
  todo sin detener el análisis; `_traducir` (línea 222) pasa el mensaje
  técnico a español.
* **Gramática:** cualquier desviación produce error del listener; el
  programa nunca se cae con excepciones no controladas (verificado con 10
  entradas malformadas).
* **Prueba:** `test_front.py` — 22 negativos + 10 de diagnóstico.
* **Ejemplo:** `python3 src/cli/main.py pruebas/negativos/n01_falta_chao.arepa`
  → rechazado con línea y columna.

## 6. Cómo se reporta línea y columna

* **Archivo:** `src/lenguaje/errores.py` (conserva `linea` y `columna` de
  ANTLR) y `src/cli/main.py` (las imprime con el formato "Línea X, Columna
  Y").
* **Prueba:** `test_front.py::probar_diagnosticos` — caso 1 verifica
  línea 2 columna 6 exactas para un `@`; caso 2 verifica que un error de
  la línea 4 se reporte en la línea 4; los 22 negativos validan posición.
* **Ejemplo:** `x = 1 @ 2` → `[léxico] Línea 2, Columna 6: Hay un símbolo
  '@' que no hace parte del lenguaje AREPA`.

## 7. Cómo se implementan asignaciones y expresiones

* **Gramática:** `asignacion` (Arepa.g4:75) y la jerarquía
  `expresion_logica → conjuncion → negacion → comparacion → aritmetica →
  termino → unario → potencia → acceso → atomo` (ya no existe `factor`),
  que codifica la precedencia documentada (`o < y < no < comparación < +- <
  */% < ^ derecha < - unario`). En particular, `^` pega más que el menos
  unario (`-2 ^ 2 = -4`) y asocia a la derecha (`2 ^ 3 ^ 2 = 512`).
* **Código propio:** `src/expresiones/evaluador.py` (`evaluar` línea 98,
  `visitAritmetica` 179) y `src/expresiones/operadores.py`; en el runtime,
  `src/runtime/ejecutor.py::visitAsignacion` (línea 160).
* **Prueba:** `test_arbol.py` (precedencia en la forma del árbol),
  `test_expresiones.py` (16 casos: `1 + 2 * 3 == 7`, `2 ^ 3 ^ 2 == 512`,
  `(1 + 2) * 3`, errores de tipos).
* **Ejemplo:** `pruebas/positivos/01_asignaciones_expresiones.arepa`.

## 8. Cómo se reconoce CSV

* **Gramática:** `instruccion_monte` (Arepa.g4:187): `monte cadena
  opciones_archivo?` con opciones `encabezado` y `separador`.
* **Código propio:** `src/runtime/ejecutor.py::_cargar` (línea 244) usa el
  lector propio `src/datos/lector_csv.py` (máquina de estados con comillas
  y escape `""`).
* **Prueba:** `test_runtime.py::monte_carga_csv_real` y los 12 casos
  `csv_*` de `test_datos.py`.
* **Ejemplo:** `ejemplos/demo.arepa` línea `ventas = monte
  "datos/ventas.csv" con encabezado, separador ","`.

## 9. Cómo se reconoce selección

* **Gramática:** alternativa `ESCOJA lista_columnas` dentro de
  `operacion_datos` (Arepa.g4:174).
* **Código propio:** `src/runtime/ejecutor.py::_aplicar_operacion`
  (línea 263, rama ESCOJA) sobre `Tabla.seleccionar`
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

## 11. Visualización (implementada desde la Fase 3)

* **Gramática:** `instruccion_grafica` (Arepa.g4:224): `pinte
  tipo_grafica identificador (clausula_estetica)* (final_grafica)?` con
  tipos `barras|lineas|histograma|dispersion|cajas`; `ejey` admite lista
  (`clausula_estetica`, Arepa.g4:237).
* **Código propio:** `src/runtime/ejecutor.py::visitInstruccion_grafica`
  (línea 502) valida la tabla y las columnas, aplica los valores por defecto
  y delega el dibujo en `src/graficas/` (motor propio).
* **Prueba:** `test_arbol.py::arbol_de_visualizacion` (estructura con
  cláusulas y cierre), negativas `n09_pinte_tipo_invalido` y
  `n13_pinte_sin_tabla`, y `pruebas/test_graficas.py` (63 casos).
* **Ejemplo:** `ejemplos/graficas.arepa` (las cinco formas).

## 12. Cómo funcionan los ciclos (ampliación del Corte 2)

* **Gramática:** `ciclo_mientras` y `ciclo_repita` (Arepa.g4): `mientras
  (cond) bloque`, `repita expr veces bloque`,
  `repita id desde expr hasta expr (paso expr)? bloque`; `pare`/`siga`
  como sentencias.
* **Código propio:** `src/runtime/ejecutor.py::visitCiclo_mientras`,
  `visitCiclo_repita` (+ `visitInstruccion_pare`/`siga` con señales
  internas `SalirCiclo`/`SeguirCiclo`); fuera de ciclo son error
  semántico con línea y columna.
* **Prueba:** `test_runtime.py` (19 casos de ciclos: acumulación,
  rangos, pasos, `pare`/`siga`, anidados, `devuelva` en función, tope
  de vueltas), `test_arbol.py::arbol_de_mientras` y
  `::arbol_de_repita`, positiva `09_ciclos.arepa`, negativas
  `n18_repita_sin_veces`, `n19_mientras_sin_parentesis`,
  `n20_repita_sin_hasta`.
* **Ejemplo:** `python src/cli/main.py ejemplos/ciclos.arepa --ejecutar`
  (factorial 120, pares 110, múltiplo 35 + pipeline + `guarde`).

## 13. Demo de estructuras en memoria (ampliación del Corte 2)

* **Gramática:** literales de estructuras propias en `atomo`:
  `lista_literal` (`[1, 2]`), `registro_literal` (`{clave: valor}`),
  `tabla_literal` (`arme [col1, col2] con [[v1, v2], [v3, v4]]`) y `acceso`
  con índices (`t[1]["col"]`); recorrido y mutación en las sentencias
  `recorra`, `agregue valor en destino` y `saque posicion de destino`.
* **Comandos:**
  `python3 src/cli/main.py ejemplos/memoria.arepa --arbol` (estructura del
  programa: 32 sentencias reconocidas) y
  `python3 src/cli/main.py ejemplos/memoria.arepa --ejecutar` (corre con la
  biblioteca propia y exporta el CSV).
* **Resultado esperado:** primer registro `Enero 120000`; total `550000`
  (coincide con el total recorrido); por categoría `Mercado: 365000`,
  `Transporte: 95000`, `Servicios: 90000`; y la evidencia
  `salidas/memoria_resumen.csv` con 3 filas (una por categoría:
  `categoria,total,promedio,registros`).
* **Qué mostrar:** los índices son 1-based, así que `gastos[1]["mes"]` es la
  primera fila (`Enero`); los registros se construyen con `{clave: valor}` y
  las listas con `[1, 2]`; `arme` crea la tabla en memoria (sin leer CSV) y
  admite una variante vacía como plantilla; `recorra fila en tabla` recorre y
  `agregue`/`saque` mutan de forma explícita; fuera de `resuma`, las
  agregaciones se calculan sobre una columna con `sume(t, col)`,
  `promedie`, `mediana`, `minimo`, `maximo`, `desviacion`, `cuente`.

---

## 14. Demo de la Fase 3 (visualización y caso de estudio)

Ruta en vivo para el Corte 3:

```bash
# 1. Las cinco gráficas desde el DSL (genera PNG en salidas/)
python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar --sin-ventana
ls -l salidas/barras.png salidas/ventas_lineas.png salidas/histograma.png \
      salidas/dispersion.png salidas/cajas.png

# 2. Caso de estudio completo (5 PNG + CSV) sobre datos públicos
AREPA_SIN_VENTANA=1 python3 src/cli/main.py caso_estudio/programa.arepa --ejecutar
ls -l caso_estudio/salidas/
# verifica: Total pasajeros: 40363

# 3. Un error con línea, columna y caret
python3 src/cli/main.py pruebas/negativos/n01_falta_chao.arepa

# 4. Ayuda y versión del CLI
python3 src/cli/main.py --ayuda
python3 src/cli/main.py --version

# 5. Regresión y conteo único
python3 pruebas/test_proyecto.py                 # 8 de 8 suites
python3 herramientas/chequeo_pruebas.py          # 8 suites, 319 pruebas
bash herramientas/regresion_programas.sh        # 170 programas (164 + 6 ejemplos)
bash herramientas/demo_sustentacion.sh           # todo de punta a punta
```

Qué mostrar:

* El **tipo de gráfica** y las cláusulas (`titulo`, `ejex`, `ejey`, `leyenda`,
  `guardela`/`muestrela`) en `gramatica/Arepa.g4:224-247`.
* Que el PNG es **propio**: `src/graficas/png.py` (chunks, CRC-32 y Adler-32
  propios, DEFLATE fijo + LZ77), sin matplotlib ni PIL.
* El **error con caret**: `n01_falta_chao.arepa` reporta `Línea 7, Columna 0` y
  señala la posición.
* El **caso de estudio**: el bloque `Archivos generados:` con los 6 archivos
  (5 PNG + 1 CSV) y el indicador `Total pasajeros: 40363`.
* Que `pruebas/test_proyecto.py` cierra con `8 de 8 suites pasaron`.

---

## Evidencia transversal

* **Matriz requisito → prueba → resultado:** `docs/05_arquitectura.md`, §8.
* **Trazabilidad funcionalidad → archivo → función → prueba:**
  `docs/05_arquitectura.md`, §10.
* **Matrices por corte:** `docs/06` (Corte 1), `docs/10` (Corte 2) y
  `docs/12` (Corte 3).
* **Informes:** `docs/04` (Fase 1), `docs/08` (Fase 2) y `docs/11` (Fase 3).
* **Manuales:** `docs/manuales/usuario.md` y `docs/manuales/tecnico.md`.
* **Cadena completa requisito → documento → gramática → código → prueba →
  ejemplo:** `docs/01` (requisitos), `docs/02` (diseño), `docs/03` (EBNF),
  `gramatica/Arepa.g4`, `src/`, `pruebas/`, `ejemplos/`.
