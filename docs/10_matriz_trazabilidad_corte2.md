# AREPA — Matriz de trazabilidad del Corte 2 (Linux)

Verificación en Linux:

```bash
python3 pruebas/test_proyecto.py
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
python3 src/cli/main.py ejemplos/memoria.arepa --ejecutar
ls -l salidas/resumen_ciudades.csv salidas/resumen_ciclos.csv salidas/filtros_listos.csv salidas/memoria_resumen.csv
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
| Validaciones semánticas | `src/errores_base.py` | `ErrorVariable/Columna/Tipos/Operacion/Semantico/Ejecucion/Archivo/CSV` | `test_expresiones.py` + `test_runtime.py` + `test_estructuras.py` (errores) |
| Lista y Registro propios | `src/datos/lista.py`, `src/datos/registro.py` | `Lista`, `Registro` (`obtener`, `poner`, `agregar`, `quitar`, `al_poner`) | `test_estructuras.py` (10 casos de lista/registro) |
| Acceso 1-based y asignación indexada | `src/datos/acceso.py` | `obtener`, `asignar`, `valores_para_fila` | `test_estructuras.py::asignacion_*`, `::lista_*`, `::registro_*` |
| Tabla en memoria (`arme`) | `src/datos/tabla.py` + `evaluador.py` | `Tabla.desde_filas`, `visitTabla_literal` | `test_estructuras.py::arme_*`, `10_estructuras.arepa` |
| Celdas y filas mutables | `src/datos/tabla.py` | `fila_como_registro`, `poner_celda`, `poner_fila` | `test_estructuras.py::asignacion_a_celda_de_tabla`, `::asignacion_a_fila_completa_*` |
| `agregue` / `saque` | `src/runtime/ejecutor.py` | `visitInstruccion_agregue`, `visitInstruccion_saque` | `test_estructuras.py` (8 casos) |
| `recorra` con snapshot | `src/runtime/ejecutor.py` | `visitCiclo_recorra` | `test_estructuras.py` (6 casos: lista, tabla, mutación, `pare`, `siga`, error) |
| Agregaciones fuera de `resuma` | `src/runtime/ejecutor.py` | `_agregacion_fuera_de_resuma`, `_calcular_sobre_valores` | `test_estructuras.py::agregaciones_de_tabla`, `::agregaciones_de_lista`, `::mediana_par_e_impar`, `::desviacion_poblacional` |
| Builtins `largo`/`columna`/`columnas` | `src/runtime/ejecutor.py` | `_largo`, `_columna`, `_columnas` | `test_estructuras.py::largo_*`, `::columna_*`, `::columnas_*` |
| Regresión pipeline en `cuenteme` | `evaluador.py::visitExpresion` + `ejecutor.py::evaluar_expresion` | callback `evaluar_expresion` | `test_estructuras.py::cuenteme_pipeline_imprime_la_tabla` |
| Regresión de precedencia | `gramatica/Arepa.g4` (`unario`, `potencia`, `acceso`) | `-2 ^ 2 = -4` | `test_estructuras.py::potencias_precedencia_y_signo`, `test_arbol.py::potencia_antes_que_menos_unario` |
| Suite de estructuras | `pruebas/test_estructuras.py` | 48 pruebas | `python3 pruebas/test_estructuras.py` → 48/48 |
| Pruebas unitarias e integración | `pruebas/` | 8 suites, 319 pruebas (conteo vigente; el Corte 3 agregó `test_graficas.py` con 63) | `python3 pruebas/test_proyecto.py` → 8/8 |

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
| Error: operación no permitida | `operacion_sin_tabla_de_entrada_rechazada`, `agregacion_sobre_columna_inexistente`, `guarde_sobre_variable_no_tabla_rechazado`, `devuelva/pare/siga` fuera de lugar | OK |
| Listas y registros en memoria | `lista_literal_y_acceso_uno_based`, `registro_literal_con_claves_id`, `registro_conserva_orden_de_claves` | OK |
| Tabla en memoria (`arme`) y acceso 1-based | `arme_con_filas`, `arme_sin_filas`, `lista_anidada_acceso_encadenado`, `acceso_a_tabla_fuera_de_rango_menciona_filas` | OK |
| Mutación explícita (D13) | `asignacion_a_lista`, `asignacion_a_celda_de_tabla`, `asignacion_a_fila_completa_con_registro`, `agregue_a_tabla_con_registro`, `saque_de_tabla` | OK |
| Recorrido con snapshot y control | `recorra_lista_acumula`, `recorra_tabla_lee_columnas`, `recorra_tabla_muta_celdas`, `recorra_con_pare`, `recorra_con_siga` | OK |
| Agregaciones en memoria | `agregaciones_de_tabla`, `agregaciones_de_lista`, `mediana_par_e_impar`, `desviacion_poblacional`, `cuente_tabla_y_columna_con_nada` | OK |
| Builtins `largo`/`columna`/`columnas` | `largo_de_tabla_lista_registro_y_texto`, `columna_devuelve_lista`, `columnas_devuelve_nombres` | OK |
| Bug pipeline en `cuenteme` corregido | `cuenteme_pipeline_imprime_la_tabla` | OK |
| Bug de precedencia `-2 ^ 2 = -4` corregido | `potencias_precedencia_y_signo`, `potencia_antes_que_menos_unario` | OK |
| Errores de estructuras | `n21_fila_incompleta`, `n22_registro_sin_dos_puntos`, `lista_indice_de_texto_rechazado`, `recorra_sobre_numero_rechazado` | OK |

## 3. Programas completos (3 exigidos; hay 6)

| Programa | Flujo | Exportación versionada |
|---|---|---|
| `ejemplos/demo.arepa` | carga → pipeline → `junte/resuma` → `pinte` (validada) → `guarde` | `salidas/resumen_ciudades.csv` (3 filas) |
| `ejemplos/ciclos.arepa` | ciclos + pipeline + `describa` + `guarde` | `salidas/resumen_ciclos.csv` (3 filas) |
| `ejemplos/filtros.arepa` | carga `;` → `escoja/renombre` → filtro + `cree` → `limpie/convierta/acomode` → `describa` + `guarde` | `salidas/filtros_listos.csv` (7 filas) |
| `ejemplos/memoria.arepa` | `arme` → acceso 1-based → `recorra` → agregaciones en memoria → `junte/resuma` → `guarde` | `salidas/memoria_resumen.csv` (3 filas) |
| `ejemplos/funciones.arepa` | `invente`, condicionales, `cuenteme`, `describa` | — |
| `ejemplos/graficas.arepa` | los cinco tipos de visualización (desde el Corte 3 genera 5 PNG reales) | `salidas/*.png` (5, Fase 3) |

Los seis validan (`python3 src/cli/main.py ejemplos/<n>.arepa`) y corren
(`--ejecutar`). Los CSV están exceptuados en `.gitignore` y se versionan
como evidencia.

---

Conteos vigentes a la fecha (Corte 3): 57 reglas, 65 reservadas, 8 suites,
319 pruebas, 170 programas. La visualización completa y el caso de estudio se
documentan en `docs/11_informe_fase3.md` y `docs/12_matriz_trazabilidad_corte3.md`.
