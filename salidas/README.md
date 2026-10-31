# Salidas (evidencia versionada de datos y ML, Linux)

Solo estos 7 archivos de evidencia están versionados (además de este
README); todo lo demás que se genere aquí es temporal e ignorado por git
(`salidas/*`).

| Archivo | Origen | Contenido |
|---|---|---|
| `resumen_ciudades.csv` | `ejemplos/demo.arepa --ejecutar` | 3 filas por ciudad (ingreso, promedio, registros) |
| `resumen_ciclos.csv` | `ejemplos/ciclos.arepa --ejecutar` | 3 filas por ciudad (ingreso, registros) |
| `filtros_listos.csv` | `ejemplos/filtros.arepa --ejecutar` | 7 filas de la encuesta limpia y ordenada |
| `regresion_casas.csv` | `ejemplos/regresion.arepa --ejecutar` | precio real y precio estimado por casa |
| `clasificacion_estudiantes.csv` | `ejemplos/clasificacion.arepa --ejecutar` | etiqueta real y predicción del perceptrón |
| `arbol_riesgo.csv` | `ejemplos/arbol_decision.arepa --ejecutar` | riesgo real y riesgo estimado por cliente |
| `.gitkeep` | — | conserva la carpeta en git |

Regenerar la evidencia desde la raíz:

```bash
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
python3 src/cli/main.py ejemplos/regresion.arepa --ejecutar
python3 src/cli/main.py ejemplos/clasificacion.arepa --ejecutar
python3 src/cli/main.py ejemplos/arbol_decision.arepa --ejecutar
```

CSV en UTF-8 sin BOM, escritos por el escritor propio
(`src/datos/escritor_csv.py`).
