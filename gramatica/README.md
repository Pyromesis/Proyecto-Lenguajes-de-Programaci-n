# Gramática AREPA (fuente única, Linux)

`Arepa.g4` es la **fuente única** del lenguaje: gramática combinada
lexer+parser para ANTLR 4.13.2 (Fases 1–2). La especificación formal
equivalente está en `docs/03_gramatica_ebnf.md`; ambas están
sincronizadas (53/53 reglas, 73 reservadas).

```bash
python3 herramientas/chequeo_gramatica.py
```

Contenido por bloques:

| Líneas | Bloque |
|---|---|
| 38–40 | `programa`: `quihubo` … `chao` con saltos obligatorios |
| 48–64 | `sentencia`: asignación, `guarde`, gráfica, condicional, ciclos, funciones, `cuenteme`, `describa`, ML, llamada |
| 74–128 | sentencias simples y bloque de machine learning (`entrene`, `evalua`, opciones) |
| 133–179 | funciones (`invente`), `fijese_si`/`sino`, `mientras`, `repita`, `pare`/`siga`, bloques |
| 182–251 | pipeline `\|>`, operaciones de datos (incluye `prediga`/`clasifique`), `monte`, columnas, etiquetas, `resuma`, tipos |
| 257–280 | visualización `pinte` + cláusulas + `guardela`/`muestrela` |
| 285–376 | expresiones con precedencia y `nombre_columna` (acepta reservadas, D5) |
| 384–527 | lexer: 73 reservadas, literales, 22 símbolos, `NL`, comentarios `#`, `ID` Unicode |

Convenciones: reservadas en minúscula sin tildes; `NL` separa
sentencias (con continuación tras `|>`, `,` y operadores); `#`
comenta hasta fin de línea. El código generado vive en `generado/`
(ver su `README.md`) y no se edita a mano.
