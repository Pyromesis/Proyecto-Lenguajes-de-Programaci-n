# Herramientas de verificación (Linux)

Scripts propios que hacen verificables los entregables. Todos corren
desde la raíz con `python3` o `bash` (ver `README.md` principal).

| Herramienta | Qué garantiza | Uso |
|---|---|---|
| `chequeo_gramatica.py` | EBNF ↔ `.g4`: 46/46 reglas y 59 reservadas | `python3 herramientas/chequeo_gramatica.py` |
| `chequeo_pruebas.py` | conteo único de pruebas: 6 suites, 194 (48+21+43+16+15+51); falla si algún total cambia | `python3 herramientas/chequeo_pruebas.py` |
| `demo_sustentacion.sh` | sustentación paso a paso (versiones, sincronía, demo, tokens/árbol, negativo, CSV, ciclos, 6/6); falla si algo no da lo esperado | `bash herramientas/demo_sustentacion.sh` |
| `consola/` | autocompletado por Tab: plugin Vim, REPL, Bash + `practica.arepa` | ver `consola/README.md` |

Los dos chequeos son la "fuente de verdad" que citan el `README.md`
principal y `docs/05_arquitectura.md`: si agregás pruebas o reglas,
actualizá el canónico en el script correspondiente.
