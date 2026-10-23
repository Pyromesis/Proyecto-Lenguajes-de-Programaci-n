# Gramática AREPA (fuente única, Linux)

`Arepa.g4` es la **fuente única** del lenguaje: gramática combinada
lexer+parser para ANTLR 4.13.2 (Fases 1–3). La especificación formal
equivalente está en `docs/03_gramatica_ebnf.md`; ambas están
sincronizadas (57/57 reglas, 65 reservadas).

```bash
python3 herramientas/chequeo_gramatica.py
```

Contenido por bloques:

| Líneas | Bloque |
|---|---|
| 38–44 | `programa` + `sentencias`: `quihubo` … `chao` con saltos obligatorios |
| 48–93 | `sentencia` y variantes simples: asignación, `guarde`, `devuelva`, `cuenteme`, `describa`, llamada |
| 95–109 | estructuras propias: `agregue`/`saque`/`recorra` |
| 111–156 | funciones (`invente`), `fijese_si`/`sino`, `mientras`, `repita`, `pare`/`siga`, `bloque` |
| 158–218 | pipeline `\|>`, operaciones de datos, `monte`, columnas, `resuma`, tipos |
| 220–247 | visualización `pinte` + cláusulas + `guardela`/`muestrela` |
| 249–383 | expresiones con precedencia (sin `factor`) y `nombre_columna` (acepta reservadas, D5) |
| 389–527 | lexer: 65 reservadas, literales, 23 símbolos, `NL`, comentarios `#`, `ID` Unicode |

Convenciones: reservadas en minúscula sin tildes; `NL` separa
sentencias (con continuación tras `|>`, `,` y operadores); `#`
comenta hasta fin de línea. El código generado vive en `generado/`
(ver su `README.md`) y no se edita a mano.
