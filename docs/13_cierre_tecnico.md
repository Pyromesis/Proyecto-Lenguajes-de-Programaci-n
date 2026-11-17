# Cierre técnico de la auditoría

La sustentación oral queda excluida por indicación del usuario. Los cinco
criterios técnicos del enunciado suman 95 puntos; su normalización a 100 es
`puntos técnicos / 95 * 100`.

| Criterio | Peso original | Peso sobre 100 | Evidencia de aceptación |
|---|---:|---:|---|
| Diseño y coherencia | 20 | 21,05 | Gramática EBNF/ANTLR sincronizada; reglas de datos y límites documentadas |
| Correctitud | 25 | 26,32 | Pruebas positivas, negativas, diagnósticos y casos adversariales |
| Implementación | 20 | 21,05 | Visitor separado por responsabilidad; lógica propia y algoritmos comprobados |
| Funcionalidad del dominio | 20 | 21,05 | Datos, estadísticas, cinco gráficas, modelos y caso público reproducible |
| Documentación y reproducibilidad | 10 | 10,53 | Manuales actualizados, verificador completo, CI y entrega íntegra SHA-256 |

## Hallazgos corregidos

| Hallazgo de la auditoría | Comportamiento corregido | Evidencia |
|---|---|---|
| Entrenamiento con tasa infinita | Se rechaza con error semántico y no se anuncia éxito | `test_tasa_infinita_no_anuncia_entrenamiento` |
| Regresión divergente con tasa 100 | Detecta aumento persistente del error y números no finitos; el modelo no queda entrenado | `test_divergencia_no_produce_nan_ni_exito`, `test_modelo_fallido_no_queda_entrenado` |
| Predicciones y métricas NaN | Validación de entradas y resultados finitos; sin convertir silenciosamente el fallo en faltantes | `test_metricas_no_aceptan_predicciones_no_finitas` |
| Columnas duplicadas ambiguas | Se rechazan en construcción, CSV y selección | Pruebas de construcción, encabezado y selección |
| Pérdida de espacios, tipos o filas en CSV | Texto citado explícito, textos ambiguos protegidos y faltantes reversibles | Ida/vuelta, 100 filas deterministas y tres separadores |
| Enteros de más de 4.300 dígitos | Conversión propia por bloques; lectura, salida y CSV sin cambiar límites globales | Literales y potencias de 5.001 dígitos |
| Ejecutor demasiado concentrado | Entrada pequeña y cinco módulos especializados con el mismo estado y Visitor | `src/runtime/ejecucion_*.py` y suites existentes |
| Entrega difícil de reproducir fuera del equipo | ZIP de archivos actuales con manifiesto, integridad y prueba en entorno virtual limpio | `test_entrega.py`, `crear_entrega.py --probar` |

Las comprobaciones también evitan falsos rechazos: pocas épocas de entrenamiento
no son un error, un objetivo constante válido funciona, y la estandarización y
las métricas manejan magnitudes extremas cuando el resultado es representable.

## Reproducir la verificación

```bash
python herramientas/verificar_entrega.py
python herramientas/crear_entrega.py --probar
```

El flujo de GitHub está preparado para Windows y Linux con Python 3.11 y 3.13.
Su ejecución remota se produce al enviar los cambios a GitHub; la comprobación
local y la prueba del ZIP son verificaciones independientes.

## Resultado del cierre

La ejecución local final aprobó **469/469 pruebas del corredor** y **370/370
pruebas internas**, en diez suites. Se aprobaron además los verificadores de
gramática, documentación y espacios del diff. Los 23 casos nuevos de auditoría
y las cuatro pruebas de integridad de la entrega están incluidos en el total.

La entrega también aprobó **469/469 pruebas y 370/370 pruebas internas** en
una carpeta nueva y un entorno virtual nuevo, instalando únicamente
`antlr4-python3-runtime==4.13.2` desde `requirements.txt`. La verificación
completa del paquete terminó con código 0.

El ZIP final se acompaña de un reporte de verificación y de su SHA-256 en
`output/entregas/`. El código, los datos y las pruebas del paquete se
contrastan con el manifiesto de la copia ejecutada en el entorno nuevo.

Con la sustentación excluida, quedan cerradas las deducciones de esta
auditoría: **95/95 puntos técnicos, equivalentes a 100/100 en los criterios
revisados**. Este resultado se refiere al alcance y a la evidencia descritos
en este documento. La matriz remota de GitHub está preparada, pero su
ejecución remota no se presenta como una comprobación ya realizada.

Las pruebas no se eliminan ni se relajan para alcanzar una calificación: los
casos que revelaron fallos quedan en el corredor y se mantienen los casos
válidos que no deben producir errores.
