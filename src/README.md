# Biblioteca propia AREPA (`src/`, Linux)

Todo el DSL es código propio del equipo **excepto** el lexer/parser
generados por ANTLR4 (ver `generado/README.md`). Sin pandas, NumPy,
Matplotlib ni equivalentes. Capas de abajo hacia arriba:
`errores_base` → `datos` → `expresiones` → `runtime` → `cli`;
solo `lenguaje/` toca el runtime de ANTLR4.

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
| `expresiones/` | `operadores.py` | aritméticos, relacionales y lógicos con validación de tipos |
| `expresiones/` | `evaluador.py` | recorre el árbol y calcula (sin `eval`/`exec`) |
| `runtime/` | `simbolos.py` | ámbitos encadenados + closures `invente` |
| `runtime/` | `contexto.py` | símbolos raíz, salida de `cuenteme`, registro de errores |
| `runtime/` | `ejecutor.py` | intérprete Visitor: pipeline, agregaciones, funciones, ciclos |
| raíz | `errores_base.py` | jerarquía `ErrorVariable/Columna/Tipos/Operacion/...` y señales de flujo |
| `cli/` | `main.py` | CLI: validar, `--arbol`, `--tokens`, `--ejecutar` (códigos 0/1/2) |
| `cli/` | `repl.py` | consola interactiva con Tab (usa `herramientas/consola/`) |

Detalle de algoritmos, decisiones y matriz
funcionalidad → archivo → función → prueba:
`docs/05_arquitectura.md`. Reglas semánticas:
`docs/09_reglas_semanticas.md`.
