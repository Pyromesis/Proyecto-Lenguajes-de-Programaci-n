# Pruebas AREPA (Linux, 319 en 8 suites)

Corredor maestro más 8 suites independientes. Todo propio, sin
bibliotecas externas para lo que se prueba.

```bash
python3 pruebas/test_proyecto.py           # las 8 suites (usa .venv si existe)
.venv/bin/python pruebas/test_graficas.py  # una suite sola (necesita antlr4)
python3 herramientas/chequeo_pruebas.py    # verifica el conteo canónico
```

El corredor maestro y `chequeo_pruebas.py` usan `.venv/bin/python`
automáticamente si existe; para correr una suite suelta, active el entorno
(`source .venv/bin/activate`) o use `.venv/bin/python`.

| Suite | Archivo | Pruebas | Qué cubre |
|---|---|---|---|
| Front-end | `test_front.py` | 55 | 10 positivos, 22 negativos, 10 de diagnóstico, 13 de CLI |
| Árbol | `test_arbol.py` | 28 | estructura y precedencia recorriendo el árbol |
| Datos | `test_datos.py` | 43 | lector CSV (12 casos), tipos, Tabla y escritor |
| Estructuras | `test_estructuras.py` | 48 | listas, registros y tablas en memoria: `arme`, acceso 1-based, `recorra`, `agregue`/`saque`, agregaciones |
| Expresiones | `test_expresiones.py` | 16 | aritmética, comparaciones, lógicos, `nada`, bordes |
| Símbolos | `test_simbolos.py` | 15 | ámbitos, closures, contexto |
| Runtime | `test_runtime.py` | 51 | programas completos (19 de ciclos) y errores semánticos |
| Gráficas | `test_graficas.py` | 63 | motor gráfico propio: PNG (20), fuente (3), lienzo (7), escalas (4), cinco dibujos (14), integración con `pinte` (11) y caso de estudio (4) |

Total: 55 + 28 + 43 + 48 + 16 + 15 + 51 + 63 = 319.

Carpetas de apoyo:

| Carpeta | Contenido |
|---|---|
| `positivos/` | 10 programas que deben aceptarse (`01`–`10`, incluye `09_ciclos` y `10_estructuras`) |
| `negativos/` | 22 programas que deben rechazarse (`n01`–`n22` con diagnóstico) |
| `datos/` | `duro.csv`, `columnas_raras.csv`, `vacia.csv` (casos borde del lector) |

Códigos del CLI verificados: 0 válido, 1 con errores, 2 no encontrado.
Trazabilidad requisito → prueba: `docs/06_matriz_trazabilidad_corte1.md`,
`docs/10_matriz_trazabilidad_corte2.md` y
`docs/12_matriz_trazabilidad_corte3.md`.
La suite de gráficas incluye la ejecución completa del caso de estudio
(`caso_estudio/programa.arepa`, 5 PNG + CSV).
