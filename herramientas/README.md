# Herramientas de verificación (Linux)

Scripts propios que hacen verificables los entregables. Todos corren
desde la raíz con `python3` o `bash` (ver `README.md` principal).

| Herramienta | Qué garantiza | Uso |
|---|---|---|
| `chequeo_gramatica.py` | EBNF ↔ `.g4`: 57/57 reglas y 65 reservadas | `python3 herramientas/chequeo_gramatica.py` |
| `chequeo_pruebas.py` | conteo único de pruebas: 8 suites, 319 (55+28+43+48+16+15+51+63); falla si algún total cambia | `python3 herramientas/chequeo_pruebas.py` |
| `chequeo_documentacion.py` | enlaces Markdown relativos, rutas antiguas, referencias `archivo.py::símbolo` (línea) y conteos 32/120/12/6; falla si algo no coincide | `python3 herramientas/chequeo_documentacion.py` |
| `regresion_programas.sh` | ejecuta los 164 ejercicios por corte y los 6 ejemplos (170 programas) con `--ejecutar --sin-ventana`; falla si alguno no termina con código 0 | `bash herramientas/regresion_programas.sh` |
| `demo_sustentacion.sh` | sustentación paso a paso (versiones, sincronía, demo, tokens/árbol, ayuda/versión, negativo con línea/columna, CSV, ciclos, estructuras en memoria, caso de estudio con 5 PNG, suite completa); falla si algo no da lo esperado | `bash herramientas/demo_sustentacion.sh` |
| `consola/` | autocompletado por Tab: plugin Vim, REPL, Bash + `practica.arepa` | ver `consola/README.md` |

Los chequeos son la "fuente de verdad" que citan el `README.md`
principal y `docs/05_arquitectura.md`: si agregás pruebas o reglas,
actualizá el canónico en el script correspondiente (la tabla `ESPERADO` de
`chequeo_pruebas.py`).
