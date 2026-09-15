# Pruebas AREPA (Linux, 194 en 6 suites)

Corredor maestro más 6 suites independientes. Todo propio, sin
bibliotecas externas para lo que se prueba.

```bash
python3 pruebas/test_proyecto.py          # las 6 suites
python3 pruebas/test_front.py             # una suite sola
python3 herramientas/chequeo_pruebas.py   # verifica el conteo canónico
```

| Suite | Archivo | Pruebas | Qué cubre |
|---|---|---|---|
| Front-end | `test_front.py` | 48 | 9 positivos, 20 negativos, 10 de diagnóstico, 9 de CLI |
| Árbol | `test_arbol.py` | 21 | estructura y precedencia recorriendo el árbol |
| Datos | `test_datos.py` | 43 | lector CSV (12 casos), tipos, Tabla y escritor |
| Expresiones | `test_expresiones.py` | 16 | aritmética, comparaciones, lógicos, `nada`, bordes |
| Símbolos | `test_simbolos.py` | 15 | ámbitos, closures, contexto |
| Runtime | `test_runtime.py` | 51 | programas completos (19 de ciclos) y errores semánticos |

Carpetas de apoyo:

| Carpeta | Contenido |
|---|---|
| `positivos/` | 9 programas que deben aceptarse (`01`–`09`, incluye `09_ciclos`) |
| `negativos/` | 20 programas que deben rechazarse (`n01`–`n20` con diagnóstico) |
| `datos/` | `duro.csv`, `columnas_raras.csv`, `vacia.csv` (casos borde del lector) |

Códigos del CLI verificados: 0 válido, 1 con errores, 2 no encontrado.
Trazabilidad requisito → prueba: `docs/06_matriz_trazabilidad_corte1.md`
y `docs/10_matriz_trazabilidad_corte2.md`.
