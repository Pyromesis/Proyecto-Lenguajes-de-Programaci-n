# Herramientas de verificación (Linux)

Scripts propios que hacen verificables los entregables. Todos corren
desde la raíz con `python3` o `bash` (ver `README.md` principal).

| Herramienta | Qué garantiza | Uso |
|---|---|---|
| `chequeo_gramatica.py` | EBNF ↔ `.g4`: 64/64 reglas y 79 reservadas | `python3 herramientas/chequeo_gramatica.py` |
| `chequeo_pruebas.py` | conteo único de pruebas: 10 suites, 370 (55+28+43+48+16+15+51+63+31+20); falla si algún total cambia | `python3 herramientas/chequeo_pruebas.py` |
| `chequeo_documentacion.py` | enlaces Markdown relativos, rutas antiguas, referencias `archivo.py::símbolo` (línea) y conteos 75/150/87/37/9; falla si algo no coincide | `python3 herramientas/chequeo_documentacion.py` |
| `partir_datos.py` | partición reproducible de un CSV en entrenamiento/prueba por SHA-256 propio (`src/utiles/sha256.py`) con lector CSV propio, sin `hashlib` ni `csv` (misma semilla → mismos archivos) | `python3 herramientas/partir_datos.py datos/casas_ml.csv` |
| `regresion_programas.sh` | ejecuta los 349 ejercicios por corte y los 9 ejemplos (358 programas) con `--ejecutar --sin-ventana`; falla si alguno no termina con código 0 | `bash herramientas/regresion_programas.sh` |
| `demo_sustentacion.sh` | sustentación paso a paso (versiones, sincronía, demo, tokens/árbol, ayuda/versión, negativo con línea/columna, CSV, ciclos, estructuras en memoria, machine learning, caso de estudio con 5 PNG, suite completa 9/9); falla si algo no da lo esperado | `bash herramientas/demo_sustentacion.sh` |
| `consola/` | autocompletado por Tab: plugin Vim, REPL, Bash + `practica.arepa` | ver `consola/README.md` |

Los chequeos son la "fuente de verdad" que citan el `README.md`
principal y `docs/05_arquitectura.md`: si agregás pruebas o reglas,
actualizá el canónico en el script correspondiente (la tabla `ESPERADO` de
`chequeo_pruebas.py`).

## Cierre técnico y entrega

`verificar_entrega.py` ejecuta gramática, documentación, corpus completo y
suites internas, deteniéndose si falla una comprobación. Funciona también
fuera de un repositorio Git.

`crear_entrega.py` incluye los archivos de trabajo actuales, genera un ZIP
reproducible, añade un manifiesto SHA-256 y comprueba la integridad. La opción
`--probar` lo instala en un entorno virtual nuevo y ejecuta allí la misma
verificación. La opción `--verificar archivo.zip` comprueba un paquete
existente; no modifica sus archivos. Las salidas están en `output/entregas/`.

```bash
python herramientas/verificar_entrega.py
python herramientas/crear_entrega.py --probar
```
