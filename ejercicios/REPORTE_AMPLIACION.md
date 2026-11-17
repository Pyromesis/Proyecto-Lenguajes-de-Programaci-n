# Verificación de la ampliación de ejercicios

Este reporte corresponde a la ampliación de ejercicios. La verificación
posterior de errores y avisos está en el
[reporte de diagnósticos](pruebas/REPORTE_DIAGNOSTICOS.md).

Fecha: 17 de noviembre de 2026. Entorno: Windows, Python 3.13.14 y
ANTLR runtime 4.13.2, sin ventanas gráficas.

## Inventario final

| Carpeta | Fáciles | Medianos | Difíciles | Adicionales | Total |
|---|---:|---:|---:|---:|---:|
| Corte 1 | 25 | 25 | 25 | 0 | 75 |
| Corte 2 | 25 | 25 | 25 | 75 de funciones | 150 |
| Corte 3 | 25 | 25 | 25 | 12 gráficas anteriores | 87 |
| Corte completo | — | — | — | 12 integradores y 25 de sustentación | 37 |
| Total | | | | | **349** |

Se añadieron **185 programas**, conservando los 164 anteriores. Cada programa
nuevo tiene enunciado, solución, resultados esperados y comando de ejecución.
Las 25 propuestas de sustentación incluyen además una respuesta razonada.

## Comprobación ejecutada

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

Terminó con **código 0**:

- **185/185** ejercicios añadidos con resultados contrastados con
  `resultados_esperados.json`.
- **55/55** casos base: ejemplos positivos, negativos, CLI y CSV multilínea.
- **174/174** programas anteriores: 164 ejercicios, nueve ejemplos y el caso
  de estudio.
- Total del corredor: **414/414** pruebas.
- Suites internas: **370/370** pruebas en **10/10** suites.

Los valores numéricos se comparan con tolerancia de `1e-7`. Se contrastan
tablas y archivos CSV; los PNG se verifican mediante firma, dimensiones,
CRC, descompresión y contenido no uniforme. Cada programa gráfico nuevo se
ejecuta dos veces y se comparan sus PNG byte a byte. Las pruebas parten de
datos y salidas temporales limpias.

La regresión de los programas anteriores comprueba análisis y ejecución sin
excepciones; los ejercicios añadidos comprueban además resultados concretos.
Los ejemplos de modelos separan entrenamiento y evaluación cuando plantean
medir predicciones sobre observaciones nuevas.

También pasaron la sincronización de gramática (64 reglas, 79 reservadas),
el verificador de documentación (enlaces, referencias, inventario y mínimo de
25 por nivel), la comprobación de sintaxis Bash del script de regresión y
`git diff --check`. Se ejecutó por la CLI la demostración de sustentación de
potencia y unario, con salida `-4 4 512`.

## Reproducir y estudiar

- [Catálogo y cobertura](CATALOGO.md).
- [Integradores y preguntas resueltas](corte_completo/README.md).
- [Índice de ejercicios](README.md).

Las preguntas son propuestas para practicar; no son preguntas oficiales del
docente. Los resultados reflejan las comprobaciones descritas y no sustituyen
la revisión de documentos ni la sustentación presencial.
