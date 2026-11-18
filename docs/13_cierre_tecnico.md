# Informe de verificación técnica

Registro de las comprobaciones realizadas el 17 de noviembre de 2026 con
Python 3.13.14 y `antlr4-python3-runtime==4.13.2`. Los comandos permiten
repetirlas sobre la copia actual del repositorio.

## Resultado registrado

| Comprobación | Resultado |
|---|---:|
| Corredor completo: ejemplos, ejercicios, diagnósticos, auditoría y entrega | 469/469 |
| Pruebas internas | 370/370 en 10 suites |
| Sincronización de gramática | 64 reglas y 79 palabras reservadas |
| Documentación | Enlaces, referencias e inventario comprobados |
| Paquete extraído en carpeta y entorno virtual nuevos | Verificación completa con código 0 |

La verificación del paquete instaló únicamente las dependencias de
`requirements.txt` y obtuvo los mismos totales de pruebas. El ZIP, su
manifiesto y el SHA-256 se generan en `output/entregas/`.

## Correcciones comprobadas

| Problema | Comportamiento verificado | Evidencia |
|---|---|---|
| Orden inestable ante claves iguales | Se conserva el orden original en empates, también en descenso y con faltantes | Ejemplos positivos 09 y 23 |
| CSV con campos multilínea | Se respetan comillas, escapes y saltos LF/CRLF; el diagnóstico conserva la primera línea física del registro | Ejemplo positivo 10 y subcasos de CSV |
| Tasa de entrenamiento infinita | Se rechaza con error semántico | `test_tasa_infinita_no_anuncia_entrenamiento` |
| Regresión divergente | Detecta el aumento persistente del error y resultados no finitos; el modelo queda sin entrenar | `test_divergencia_no_produce_nan_ni_exito`, `test_modelo_fallido_no_queda_entrenado` |
| Predicciones o métricas no finitas | Se validan entradas y resultados | `test_metricas_no_aceptan_predicciones_no_finitas` |
| Columnas duplicadas | Se rechazan en construcción, lectura CSV y selección | Casos de `test_auditoria.py` |
| Pérdida de texto o filas en CSV | Se conservan espacios, comillas, textos ambiguos y faltantes | Ida y vuelta con 100 filas y tres separadores |
| Enteros extensos | Conversión por bloques sin modificar límites globales de Python | Literales y potencias de 5.001 dígitos |
| Ejecutor concentrado en un módulo | Visitor distribuido en cinco módulos que comparten el contexto | Suites de ejecución y `src/runtime/ejecucion_*.py` |
| Entrega no reproducible | ZIP determinista con manifiesto y comprobación de integridad | `test_entrega.py` y prueba en entorno virtual nuevo |

También se comprueban casos válidos: pocas épocas de entrenamiento, objetivos
constantes y magnitudes extremas cuyo resultado es representable. La división
por cero y otras operaciones especiales permitidas generan avisos; los
diagnósticos se verifican sin convertir esos casos en errores.

## Historial de verificación

Los siguientes hitos consolidan los reportes iniciales, de ampliación y de
diagnósticos. Los totales reflejan la cobertura disponible en cada etapa.

| Etapa | Pruebas del corredor | Pruebas internas |
|---|---:|---:|
| Verificación inicial de ejemplos y programas existentes | 229 | 370 |
| Incorporación de 185 ejercicios con resultados esperados | 414 | 370 |
| Ampliación de diagnósticos de consola | 442 | 370 |
| Casos adversariales e integridad del paquete | 469 | 370 |

## Reproducción

Desde la raíz del proyecto, con las dependencias instaladas:

```bash
python ejercicios/pruebas/ejecutar.py --completo
python herramientas/verificar_entrega.py
python herramientas/crear_entrega.py --probar
```

La [guía de pruebas](../ejercicios/pruebas/README.md) describe las
comparaciones numéricas, de tablas, CSV y PNG. La
[guía de herramientas](../herramientas/README.md) detalla los chequeos y
el empaquetado.

La configuración de GitHub Actions contempla Python 3.11 y 3.13. Este informe registra la ejecución local y la del
paquete extraído; no acredita una ejecución remota de esa matriz.
