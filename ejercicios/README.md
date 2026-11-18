# Ejercicios y problemas AREPA

**349 programas resueltos**, organizados por corte, dificultad e integración.
Los cortes 1, 2 y 3 tienen **al menos 25 ejercicios fáciles, 25 medianos y
25 difíciles cada uno**. Se conservan los 75 ejercicios de funciones y los
12 ejercicios gráficos anteriores.

| Carpeta | Fáciles | Medianos | Difíciles | Adicionales | Total |
|---|---:|---:|---:|---:|---:|
| [Corte 1](corte1/README.md) | 25 | 25 | 25 | — | 75 |
| [Corte 2](corte2/README.md) | 25 | 25 | 25 | 75 de funciones | 150 |
| [Corte 3](corte3/README.md) | 25 | 25 | 25 | 12 gráficas | 87 |
| [Corte completo](corte_completo/README.md) | — | — | — | 12 integradores y 25 de sustentación | 37 |

Los **185 ejercicios añadidos** contienen enunciado, solución completa,
resultados esperados y el comando para ejecutarlos. El [catálogo](CATALOGO.md)
explica la cobertura. Los programas de sustentación incluyen además una
respuesta razonada: son propuestas de práctica, no preguntas oficiales.

El [reporte de verificación](../docs/13_cierre_tecnico.md) registra la ejecución completa.

## Ejecutar un ejercicio

Desde la raíz del proyecto:

```bash
python src/cli/main.py ejercicios/corte1/faciles/F12_potencia_cuadrado.arepa --ejecutar
python src/cli/main.py ejercicios/corte3/medianos/M20_funcion_cuadratica.arepa --ejecutar --sin-ventana
python src/cli/main.py ejercicios/corte_completo/integradores/I12_pasajeros_publicos.arepa --ejecutar --sin-ventana
```

Los que usan `guarde` o `guardela` escriben en `salidas/`. Las rutas de
`datos/`, `ejercicios/datos/` y `caso_estudio/datos/` se resuelven desde la raíz.
Solo se necesita la dependencia ANTLR de `requirements.txt`.

## Contenido

- Corte 1: sintaxis, literales, operadores, potencia, precedencia, lógica,
  selección, filtros y primeros pipelines.
- Corte 2: símbolos, funciones, recursión, ciclos, listas, registros, tablas,
  mutación, limpieza, conversión, agrupación, estadísticas y CSV.
- Corte 3: 25 ejercicios por nivel con barras, líneas, histogramas, dispersión,
  cajas, ejes, títulos, leyendas, series, exportación, modelos y análisis.
- Corte completo: ventas y encuestas con datos del proyecto, inventario,
  informe académico, simulaciones, regresión, clasificación, calidad,
  estadísticas robustas y el caso público de pasajeros con cinco gráficas.
- Sustentación: 25 preguntas resueltas sobre decisiones del lenguaje,
  diferencias entre construcciones y explicación de resultados.

## Pruebas y regresión

```bash
# 110 casos: base, diagnósticos, auditoría y entrega
python ejercicios/pruebas/ejecutar.py

# 295 casos: los anteriores y resultados de los 185 ejercicios nuevos
python ejercicios/pruebas/ejecutar.py --ejercicios

# Todo: 349 ejercicios, nueve ejemplos, caso de estudio y suites internas
python ejercicios/pruebas/ejecutar.py --completo

# Alternativa Bash: 358 programas correctos por CLI
bash herramientas/regresion_programas.sh
```

El corredor compara tablas y valores con `resultados_esperados.json`, lee los
CSV exportados y verifica PNG válidos y reproducibles en carpetas temporales.
Los [ejemplos de prueba](pruebas/README.md) también incluyen 29 programas que
**deben fallar**; el script Bash los excluye de la regresión positiva.

Para verificar enlaces, conteos y el mínimo por nivel:

```bash
python herramientas/chequeo_documentacion.py
```
