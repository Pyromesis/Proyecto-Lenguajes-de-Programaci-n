# AREPA — Matriz de trazabilidad del Corte 2 (Linux)

Verificación en Linux:

```bash
python3 pruebas/test_proyecto.py
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
ls -l salidas/resumen_ciudades.csv salidas/resumen_ciclos.csv salidas/filtros_listos.csv
```

Reglas aplicadas: `docs/09_reglas_semanticas.md`.
Motor: `docs/05_arquitectura.md` (§4–§6).

## 1. Actividades del Corte 2

| Actividad del enunciado | Módulo (archivo) | Función / clase | Prueba |
|---|---|---|---|
| Patrón Visitor en Python | `src/runtime/ejecutor.py` | `EjecutorArepa(ArepaVisitor)` | `test_runtime.py` (51) |
| Patrón Visitor en expresiones | `src/expresiones/evaluador.py` | `EvaluadorExpresiones(ArepaVisitor)` | `test_expresiones.py` (16) |
| Contexto de ejecución | `src/runtime/contexto.py` | `ContextoEjecucion` | `test_simbolos.py::contexto_reune_simbolos_salida_y_tablas` |
| Tabla de símbolos | `src/runtime/simbolos.py` | `TablaSimbolos`, `FuncionArepa` | `test_simbolos.py` (15) |
| Asociar identificadores con datos | `ejecutor.py::visitAsignacion`, `evaluador.py::_resolver_nombre` | columna → variable → `ErrorVariable` | `test_runtime.py::variable_inexistente_rechazada` |
| Carga | `ejecutor.py::_cargar` + `datos/lector_csv.py` | `LectorCSV.leer` (UTF-8, BOM tolerado) | `test_runtime.py::monte_carga_csv_real` |
| Selección | `datos/tabla.py` | `Tabla.seleccionar` | `test_runtime.py::escoja_selecciona_columnas` |
| Filtrado | `datos/tabla.py` | `Tabla.filtrar` | `test_runtime.py::deje_donde_filtra_filas` |
| Ordenamiento | `datos/tabla.py` | `Tabla.ordenar` (merge sort) | `test_datos.py::tabla_ordenamiento_estable_por_dos_claves` |
| Columnas calculadas | `datos/tabla.py` | `Tabla.crear_columna` | `test_runtime.py::pipeline_completo_con_cree` |
| Datos faltantes | `datos/tabla.py` | `quitar_duplicados`, `rellenar_vacios`, `eliminar_filas_con_vacios` | `test_runtime.py::limpie_duplicados_y_vacios` |
| Renombre / conversión | `datos/tabla.py` | `renombrar`, `convertir_columna` | `test_runtime.py::convierta_tipo_de_columna` |
| Agrupamiento + agregaciones | `datos/tabla.py` + `ejecutor.py` | `Tabla.agrupar`, `_ejecutar_resuma`, `_calcular_agregacion` | `test_runtime.py::junte_resuma_agregaciones` |
| Estadísticas descriptivas | `ejecutor.py` | `visitInstruccion_describa` | `test_runtime.py::describa_produce_resumen_propio` |
| Escritura CSV | `datos/escritor_csv.py` | `EscritorCSV.escribir` (UTF-8) | `test_runtime.py::guarde_escribe_csv_legible` |
| Validaciones semánticas | `src/errores_base.py` | `ErrorVariable/Columna/Tipos/Operacion/Semantico/Ejecucion/Archivo/CSV` | `test_expresiones.py` + `test_runtime.py` (errores) |
| Pruebas unitarias e integración | `pruebas/` | 6 suites, 194 pruebas | `python3 pruebas/test_proyecto.py` → 6/6 |

## 2. Alcance mínimo del Corte 2

| Alcance exigido | Evidencia | Resultado |
|---|---|---|
| Lectura y almacenamiento tabular | `monte_carga_csv_real` (12 filas `datos/ventas.csv`), 12 casos `csv_*` | OK |
| Selección, filtrado, creación de columnas | `escoja_selecciona_columnas`, `deje_donde_filtra_filas`, `pipeline_completo_con_cree` | OK |
| Agrupamiento y agregaciones | `junte_resuma_agregaciones`, `agregaciones_estadisticas_propias`, `agregaciones_en_tabla_vacia_dan_nada` | OK |
| Estadísticas descriptivas | `describa_produce_resumen_propio` | OK |
| Escritura de resultados en CSV | `salidas/resumen_ciudades.csv` (demo), `salidas/resumen_ciclos.csv` (ciclos), `salidas/filtros_listos.csv` (filtros) | OK |
| Error: variable inexistente | `variable_inexistente_rechazada` | OK |
| Error: columna inexistente | `escoja_columna_inexistente`, `agregacion_sobre_columna_inexistente`, `pinte_valida_columnas_de_la_grafica` | OK |
| Error: tipos incompatibles | `suma_numero_mas_texto_rechazada`, `comparacion_numero_con_texto_rechazada`, `logico_con_numero_rechazado` | OK |
| Error: operación no permitida | `operacion_sin_tabla_de_entrada_rechazada`, `agregacion_fuera_de_resuma_rechazada`, `guarde_sobre_variable_no_tabla_rechazado`, `devuelva/pare/siga` fuera de lugar | OK |

## 3. Programas completos (3 exigidos)

| Programa | Flujo | Exportación versionada |
|---|---|---|
| `ejemplos/demo.arepa` | carga → pipeline → `junte/resuma` → `pinte` (validada) → `guarde` | `salidas/resumen_ciudades.csv` (3 filas) |
| `ejemplos/ciclos.arepa` | ciclos + pipeline + `describa` + `guarde` | `salidas/resumen_ciclos.csv` (3 filas) |
| `ejemplos/filtros.arepa` | carga `;` → `escoja/renombre` → filtro + `cree` → `limpie/convierta/acomode` → `describa` + `guarde` | `salidas/filtros_listos.csv` (7 filas) |

Los tres validan (`python3 src/cli/main.py ejemplos/<n>.arepa`) y corren
(`--ejecutar`). Los CSV están exceptuados en `.gitignore` y se versionan
como evidencia.
