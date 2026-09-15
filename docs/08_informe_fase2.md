# AREPA — Informe de la Fase 2: Semántica y procesamiento de datos

**Proyecto:** Lenguaje de dominio específico para ciencia de datos y visualización
**Curso:** Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2
**Fase entregada:** Corte 2 — Semántica y procesamiento de datos (acumulativa sobre el Corte 1)

Este documento mapea cada exigencia del Corte 2 del enunciado a su evidencia
verificable en el repositorio. Todo se comprueba con:

```bash
python pruebas/test_proyecto.py   # 6 suites, 194 pruebas, todas pasan
```

---

## 1. Actividades del Corte 2 y dónde quedaron

| Actividad del enunciado | Evidencia |
|---|---|
| Implementar el patrón Visitor en Python | `src/runtime/ejecutor.py::EjecutorArepa(ArepaVisitor)`, `src/expresiones/evaluador.py::EvaluadorExpresiones(ArepaVisitor)` |
| Diseñar el contexto de ejecución y la tabla de símbolos | `src/runtime/contexto.py::ContextoEjecucion`, `src/runtime/simbolos.py::TablaSimbolos` (ámbitos padre→hijo, closures) |
| Asociar identificadores con objetos de datos | `ejecutor.py::visitAsignacion` + `evaluador.py::_resolver_nombre` (columna de la fila en contexto → variable → `ErrorVariable` con columnas disponibles) |
| Carga | `monte` → `ejecutor.py::_cargar` + `src/datos/lector_csv.py` (máquina de estados propia: comillas, escape `""`, separador configurable, BOM tolerado) |
| Selección | `escoja` → `Tabla.seleccionar` |
| Filtrado | `deje donde` → `Tabla.filtrar` (conserva la fila solo si la condición es exactamente `obvio`) |
| Ordenamiento | `acomode` → `Tabla.ordenar` (merge sort propio y estable; `nada` al final) |
| Columnas calculadas | `cree` → `Tabla.crear_columna` |
| Tratamiento de datos faltantes | `limpie duplicados` / `limpie vacios (con VALOR)?` → `quitar_duplicados`, `rellenar_vacios`, `eliminar_filas_con_vacios` |
| Renombre y conversión (preparación) | `renombre COL -> NUEVA`, `convierta COL -> tipo` (calendario propio AAAA-MM-DD) |
| Agrupamiento y agregaciones | `junte por` + `resuma` → `Tabla.agrupar` + `cuente/sume/promedie/mediana/minimo/maximo/desviacion` propios (mediana por inserción, desviación poblacional) |
| Validaciones semánticas | `src/errores_base.py` (`ErrorVariable`, `ErrorColumna`, `ErrorTipos`, `ErrorOperacion`, `ErrorSemantico`, `ErrorEjecucion`, `ErrorArchivo`, `ErrorCSV`) |
| Pruebas | `pruebas/test_proyecto.py` (corredor) + 6 suites: front-end 48, árbol 21, datos 43, expresiones 16, símbolos 15, runtime 51 |

Detalle de algoritmos y decisiones: `docs/05_arquitectura.md`.

---

## 2. Alcance mínimo de la versión (Corte 2) y su verificación

| Alcance mínimo exigido | Verificación |
|---|---|
| Lectura y almacenamiento de datos tabulares | `test_runtime.py::monte_carga_csv_real` (12 filas de `datos/ventas.csv`), `test_datos.py` (12 casos `csv_*`); `guarde` escribe CSV legible que se relee (`guarde_escribe_csv_legible`) |
| Selección, filtrado y creación de columnas | `escoja_selecciona_columnas`, `deje_donde_filtra_filas`, `pipeline_completo_con_cree` |
| Agrupamiento y agregaciones | `junte_resuma_agregaciones`, `agregaciones_estadisticas_propias`, `agregaciones_en_tabla_vacia_dan_nada` |
| Estadísticas descriptivas | `describa` → `describa_produce_resumen_propio` (`sume/promedie/mediana/minimo/maximo/desviacion` por columna numérica) |
| Escritura de resultados en CSV | `ejemplos/demo.arepa --ejecutar` genera `salidas/resumen_ciudades.csv`; `ejemplos/ciclos.arepa --ejecutar` genera `salidas/resumen_ciclos.csv`; `ejemplos/filtros.arepa --ejecutar` genera `salidas/filtros_listos.csv` (los 3 versionados, exceptuados en `.gitignore`) |
| Errores por variables inexistentes | `variable_inexistente_rechazada` |
| Errores por columnas inexistentes | `escoja_columna_inexistente`, `agregacion_sobre_columna_inexistente`, `pinte_valida_columnas_de_la_grafica` |
| Errores por tipos incompatibles | `suma_numero_mas_texto_rechazada`, `comparacion_numero_con_texto_rechazada`, `logico_con_numero_rechazado` (en `test_expresiones.py`) |
| Errores por operaciones no permitidas | `operacion_sin_tabla_de_entrada_rechazada`, `agregacion_fuera_de_resuma_rechazada`, `guarde_sobre_variable_no_tabla_rechazado`, `devuelva_fuera_de_funcion_rechazado`, `pare/siga` fuera de ciclo |

---

## 3. Programas completos (mínimo 3 exigidos; hay 5)

| Programa | Qué ejercita |
|---|---|
| `ejemplos/demo.arepa` | flujo completo: carga, pipeline, resumen por ciudad, gráfica (validada), guardado |
| `ejemplos/filtros.arepa` | carga, selección, filtros, limpieza y orden |
| `ejemplos/funciones.arepa` | `invente`, condicionales, `cuenteme`, `describa` |
| `ejemplos/graficas.arepa` | los cinco tipos de visualización (validación) |
| `ejemplos/ciclos.arepa` | ciclos + pipeline + `describa` + `guarde` |

Todos validan (`python src/cli/main.py ejemplos/<nombre>.arepa`) y corren
(`--ejecutar`). Evidencia de transformación y exportación: `salidas/*.csv`.

---

## 4. Ampliación del Corte 2: ciclos `mientras` / `repita` con `pare` / `siga`

El enunciado solo exige funciones y condicionales; los ciclos se añaden como
**ampliación acotada** (decisión D11 en `docs/02_catalogo_instrucciones.md`):
acumulaciones iterativas y búsquedas con parada temprana sin recursión manual,
sin convertir el DSL en una copia de Python (no hay `for` estilo C).

* Gramática: `ciclo_mientras`, `ciclo_repita`, `instruccion_pare`,
  `instruccion_siga` en `gramatica/Arepa.g4` (+8 reservadas: 51 → 59);
  código regenerado en `generado/` con ANTLR 4.13.2.
* Semántica: `docs/02` §3.6 y `docs/05` §6 (condición lógica, conteo entero
  ≥ 0, rango inclusive con paso por defecto 1/-1, sin ámbito propio en el
  bloque, `pare`/`siga` solo dentro de ciclo, tope de 1 000 000 de vueltas).
* Pruebas: 19 casos en `test_runtime.py` + positiva `09_ciclos.arepa` +
  negativas `n18` (sin `veces`), `n19` (sin paréntesis), `n20` (sin `hasta`).

---

## 5. Requisitos técnicos (según enunciado) y su estado

| Requisito | Estado |
|---|---|
| ANTLR4 para lexer y parser | `antlr4-python3-runtime==4.13.2`; regeneración con `generar_gramatica.sh` (Linux, verificado con JDK 17) |
| Python 3.11+ | probado con 3.12/3.13 |
| Patrón Visitor | `EjecutorArepa` y `EvaluadorExpresiones` extienden `ArepaVisitor` |
| Bibliotecas sugeridas (pandas, NumPy, Matplotlib) | **no se usan**: toda la lógica es propia (`docs/05_arquitectura.md`); el enunciado las presenta como apoyo opcional ("podrán emplearse") |
| Git + remoto | historial en `git log`; rama `main` |
| Dependencias | `requirements.txt` (solo `antlr4-python3-runtime`) |
| CLI | `src/cli/main.py` (códigos 0/1/2, `--arbol`, `--tokens`, `--ejecutar`); REPL opcional en `src/cli/repl.py` |
| Datos de ejemplo | `datos/ventas.csv`, `datos/encuesta.csv`, `datos/empleados.csv` |

**Producto del corte:** el DSL procesa datos reales y produce una tabla
resumen correctamente exportada (p. ej. `salidas/resumen_ciudades.csv` con
3 filas por ciudad desde `datos/ventas.csv`).

---

## 6. Verificación automática adicional (reproducibilidad)

| Herramienta | Qué garantiza | Cómo correrla |
|---|---|---|
| `herramientas/chequeo_gramatica.py` | EBNF ↔ `.g4`: 46/46 reglas y 59 reservadas en ambas direcciones (hace real el "chequeo" citado en `docs/06` R10/R23) | `python herramientas/chequeo_gramatica.py` |
| `herramientas/demo_sustentacion.sh` | evidencia de sustentación paso a paso (versiones, sincronía, demo, tokens/árbol, negativo con línea/columna, ejecución + CSV, ciclos, suite 6/6); falla si algo no da lo esperado | `bash herramientas/demo_sustentacion.sh` |
| Tubería cerrada | `arepa demo.arepa --arbol \| head` sale limpio (código 0, sin volcado) en Linux | `test_front.py` CLI: "tubería cerrada sale limpio sin traceback" |
