# Reporte de verificación inicial

Este reporte conserva la validación previa a la ampliación de ejercicios.
El catálogo vigente está en [../CATALOGO.md](../CATALOGO.md).

Fecha: 17 de noviembre de 2026. Entorno: Windows, Python 3.13.14,
ANTLR runtime 4.13.2. Ejecución sin ventanas gráficas.

## Resultado

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

Terminó con código **0**.

| Grupo | Resultado |
|---|---:|
| Ejemplos positivos con resultados esperados | 24/24 |
| Ejemplos negativos con rechazo esperado | 29/29 |
| Comprobaciones adicionales de CLI y CSV multilínea | 2/2, con varios subcasos |
| Ejercicios existentes de los tres cortes | 164/164 |
| Ejemplos existentes | 9/9 |
| Caso de estudio completo | 1/1 |
| Total del corredor nuevo, incluida regresión | **229/229** |
| Pruebas internas originales | **370/370 en 10 suites** |

La regresión de los 174 programas existentes comprueba análisis y ejecución
sin excepciones. Los 24 ejemplos nuevos comparan resultados concretos según
`esperados.json`, con tolerancia numérica de `1e-7`. Los PNG se verifican y
se regeneran para comprobar determinismo; los CSV se contrastan con el lector
estándar de Python.

También pasaron `herramientas/chequeo_gramatica.py` (64 reglas y 79
reservadas), `herramientas/chequeo_documentacion.py`,
`herramientas/chequeo_pruebas.py` y `git diff --check`.

## Fallos encontrados y corregidos

1. **Ordenamiento inestable ante claves iguales.** La mezcla elegía primero
   la fila de la mitad derecha cuando había empate. Ahora conserva la fila
   izquierda primero y respeta el orden original. Los ejemplos 09 y 23
   comprueban empates, dos claves, descenso y faltantes.
2. **CSV con campos multilínea.** El lector dividía cada salto físico como
   un registro nuevo, por lo que no podía releer algunos archivos que el
   escritor propio generaba. Ahora separa registros respetando campos entre
   comillas, escapes y saltos LF/CRLF, y conserva la línea física inicial para
   los diagnósticos. El ejemplo 10 verifica exportación y relectura; los
   subcasos adicionales verifican separadores, líneas vacías dentro de campos
   y errores con comillas sin cerrar.

Estos resultados corresponden al código y los datos revisados en esta fecha.
La documentación, el historial de Git y la sustentación requieren además
revisión humana según los criterios del curso.
