# Gramática AREPA (fuente única, Linux)

`Arepa.g4` es la **fuente única** del lenguaje: gramática combinada
lexer+parser para ANTLR 4.13.2 (Fases 1–2). La especificación formal
equivalente está en `docs/03_gramatica_ebnf.md`; ambas están
sincronizadas (46/46 reglas, 59 reservadas).

```bash
python3 herramientas/chequeo_gramatica.py
```

Contenido por bloques:

| Líneas | Bloque |
|---|---|
| 38–40 | `programa`: `quihubo` … `chao` con saltos obligatorios |
| 48–62 | `sentencia`: asignación, `guarde`, gráfica, condicional, ciclos, funciones, `cuenteme`, `describa`, llamada |
| 95–137 | funciones (`invente`), `fijese_si`/`sino`, `mientras`, `repita`, `pare`/`siga`, bloques |
| 144–199 | pipeline `\|>`, operaciones de datos, `monte`, columnas, `resuma`, tipos |
| 205–228 | visualización `pinte` + cláusulas + `guardela`/`muestrela` |
| 233–321 | expresiones con precedencia y `nombre_columna` (acepta reservadas, D5) |
| 329–455 | lexer: 59 reservadas, literales, 22 símbolos, `NL`, comentarios `#`, `ID` Unicode |

Convenciones: reservadas en minúscula sin tildes; `NL` separa
sentencias (con continuación tras `|>`, `,` y operadores); `#`
comenta hasta fin de línea. El código generado vive en `generado/`
(ver su `README.md`) y no se edita a mano.
