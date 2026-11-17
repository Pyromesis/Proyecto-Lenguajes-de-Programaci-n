# Biblioteca propia AREPA (`src/`, Linux)

Todo el DSL es código propio del equipo **excepto** el lexer/parser
generados por ANTLR4 (ver `generado/README.md`). Sin pandas, NumPy,
Matplotlib ni equivalentes. Capas de abajo hacia arriba:
`errores_base` → `datos` → `graficas` → `expresiones` → `runtime` → `cli`;
`lenguaje/` orquesta el lexer y el parser; `expresiones/` y `runtime/`
recorren el árbol heredando del Visitor generado por ANTLR4.

| Módulo | Archivo | Responsabilidad |
|---|---|---|
| `lenguaje/` | `analizador.py` | orquesta lexer+parser ANTLR y devuelve `(parser, árbol, errores)` |
| `lenguaje/` | `errores.py` | listener propio: traduce diagnósticos a español con línea/columna |
| `lenguaje/` | `arbol.py` | impresión jerárquica del árbol y conteo de sentencias |
| `datos/` | `tabla.py` | `Tabla` central: selección, filtrado, merge sort propio, columnas, vacíos, agrupamiento |
| `datos/` | `columna.py` / `fila.py` | metadato nombre+tipo y registro de valores |
| `datos/` | `lector_csv.py` | máquina de estados CSV propia (comillas, `""`, separador, BOM) |
| `datos/` | `escritor_csv.py` | escritura CSV propia UTF-8 para `guarde` |
| `datos/` | `tipos.py` | valores (`nada`, infinitos), conversiones y calendario propio |
| `datos/` | `lista.py` / `registro.py` | `Lista` y `Registro` propios de `arme` (sin `dict`/`OrderedDict`) |
| `datos/` | `acceso.py` | acceso indexado 1-based compartido por evaluador y ejecutor |
| `graficas/` | `png.py` | escritor PNG propio (DEFLATE, CRC-32 y Adler-32 caseros) |
| `graficas/` | `lienzo.py` | búfer RGB propio con píxel, línea, rectángulo, círculo y texto |
| `graficas/` | `fuente.py` | fuente bitmap 5x7 propia (sin fuentes del sistema) |
| `graficas/` | `escalas.py` | `EscalaLineal`/`EscalaBanda` y ticks "bonitos" |
| `graficas/` | `tipos_grafica.py` | motor de las 5 gráficas (`barras`, `lineas`, `histograma`, `dispersion`, `cajas`) |
| `expresiones/` | `operadores.py` | aritméticos, relacionales y lógicos con validación de tipos |
| `expresiones/` | `evaluador.py` | recorre el árbol y calcula (sin `eval`/`exec`) |
| `runtime/` | `simbolos.py` | ámbitos encadenados + closures `invente` |
| `runtime/` | `contexto.py` | símbolos raíz, salida de `cuenteme`, registro de errores y archivos |
| `runtime/` | `ejecutor.py` | entrada del Visitor: contexto, símbolos y coordinación de expresiones |
| `runtime/` | `ejecucion_datos.py` | carga, pipelines, agrupación, estadísticas y exportación CSV |
| `runtime/` | `ejecucion_graficas.py` | validación de cláusulas, creación y publicación de PNG |
| `runtime/` | `ejecucion_control.py` | condicionales, ciclos, funciones y llamadas |
| `runtime/` | `ejecucion_estructuras.py` | mutación, índices y funciones de listas, registros y tablas |
| `runtime/` | `ejecucion_modelos.py` | opciones de entrenamiento, predicción y evaluación |
| `utiles/` | `enteros.py` | conversión decimal por bloques, incluidos enteros de más de 4.300 dígitos |
| `utiles/` | `matematica.py` | `piso`, `techo`, `raiz_entera`, `raiz_cuadrada`, `exponente_decimal`, `es_finito` (sin `math`) |
| `utiles/` | `texto.py` | `es_identificador`, `colapsar_espacios`, `quitar_tildes` con tabla propia (sin `re` ni `unicodedata`) |
| `utiles/` | `binario.py` | enteros ↔ bytes big/little-endian con desplazamientos (sin `struct`) |
| `utiles/` | `sha256.py` | SHA-256 propio con constantes calculadas (sin `hashlib`); lo usa `herramientas/partir_datos.py` |
| raíz | `errores_base.py` | jerarquía `ErrorVariable/Columna/Tipos/Operacion/...` y señales de flujo |
| `cli/` | `main.py` | CLI: validar, `--arbol`, `--tokens`, `--ejecutar` (códigos 0/1/2); analizador de argumentos propio (sin `argparse`) |
| `cli/` | `repl.py` | consola interactiva con Tab (usa `herramientas/consola/`) |

Detalle de algoritmos, decisiones y matriz
funcionalidad → archivo → función → prueba:
`docs/05_arquitectura.md`. Reglas semánticas:
`docs/09_reglas_semanticas.md`.
