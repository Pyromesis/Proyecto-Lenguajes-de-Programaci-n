# Salidas (evidencia versionada del Corte 2, Linux)

Solo estos 4 archivos están versionados (exceptuados en `.gitignore`);
todo lo demás que se genere aquí es temporal e ignorado por git
(`salidas/*`).

| Archivo | Origen | Contenido |
|---|---|---|
| `resumen_ciudades.csv` | `ejemplos/demo.arepa --ejecutar` | 3 filas por ciudad (ingreso, promedio, registros) |
| `resumen_ciclos.csv` | `ejemplos/ciclos.arepa --ejecutar` | 3 filas por ciudad (ingreso, registros) |
| `filtros_listos.csv` | `ejemplos/filtros.arepa --ejecutar` | 7 filas de la encuesta limpia y ordenada |
| `.gitkeep` | — | conserva la carpeta en git |

Regenerar la evidencia desde la raíz:

```bash
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
```

CSV en UTF-8 sin BOM, escritos por el escritor propio
(`src/datos/escritor_csv.py`).
