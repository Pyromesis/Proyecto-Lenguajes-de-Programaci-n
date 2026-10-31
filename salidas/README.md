# Salidas (evidencia versionada de datos, estructuras y ML, Linux)

Solo estos 7 archivos de evidencia están versionados (además de este
README); todo lo demás que se genere aquí es temporal e ignorado por git
(`salidas/*`).

## CSV versionados

| Archivo | Origen | Contenido |
|---|---|---|
| `resumen_ciudades.csv` | `ejemplos/demo.arepa --ejecutar` | 3 filas por ciudad (ingreso, promedio, registros) |
| `resumen_ciclos.csv` | `ejemplos/ciclos.arepa --ejecutar` | 3 filas por ciudad (ingreso, registros) |
| `filtros_listos.csv` | `ejemplos/filtros.arepa --ejecutar` | 7 filas de la encuesta limpia y ordenada |
| `memoria_resumen.csv` | `ejemplos/memoria.arepa --ejecutar` | 3 filas por categoría (total, promedio, registros) |
| `regresion_casas.csv` | `ejemplos/regresion.arepa --ejecutar` | precio real y precio estimado por casa |
| `clasificacion_estudiantes.csv` | `ejemplos/clasificacion.arepa --ejecutar` | etiqueta real y predicción del perceptrón |
| `arbol_riesgo.csv` | `ejemplos/arbol_decision.arepa --ejecutar` | riesgo real y riesgo estimado por cliente |
| `.gitkeep` | — | conserva la carpeta en git |

CSV en UTF-8 sin BOM, escritos por el escritor propio
(`src/datos/escritor_csv.py`).

## PNG temporales (no versionados)

Los ejemplos de gráficas escriben PNG aquí al ejecutarse; son
temporales e ignorados por git, pero evidencian la Fase 3:

| Archivo | Origen | Contenido |
|---|---|---|
| `ingresos_ciudad.png` | `ejemplos/demo.arepa --ejecutar` | barras de ingreso por ciudad (800x480) |
| `barras.png` | `ejemplos/graficas.arepa --ejecutar` | barras de unidades por fecha |
| `ventas_lineas.png` | `ejemplos/graficas.arepa --ejecutar` | líneas de unidades por fecha (de `muestrela`) |
| `histograma.png` | `ejemplos/graficas.arepa --ejecutar` | distribución de unidades |
| `dispersion.png` | `ejemplos/graficas.arepa --ejecutar` | precio frente a unidades |
| `cajas.png` | `ejemplos/graficas.arepa --ejecutar` | rango de precios por ciudad |
| `ej_g*.png` | `ejercicios/corte3/graficas/*.arepa` | evidencias de los 12 ejercicios de visualización |

## Regenerar la evidencia desde la raíz

```bash
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
python3 src/cli/main.py ejemplos/memoria.arepa --ejecutar
python3 src/cli/main.py ejemplos/regresion.arepa --ejecutar
python3 src/cli/main.py ejemplos/clasificacion.arepa --ejecutar
python3 src/cli/main.py ejemplos/arbol_decision.arepa --ejecutar
python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar --sin-ventana
```

El caso de estudio del Corte 3 **no** escribe aquí: sus CSV y PNG
quedan en `caso_estudio/salidas/` (ver `caso_estudio/README.md`).
