# Gramática AREPA (fuente única, Linux)

`Arepa.g4` es la **fuente única** del lenguaje: gramática combinada
lexer+parser para ANTLR 4.13.2 (Fases 1–3). La especificación formal
equivalente está en `docs/03_gramatica_ebnf.md`; ambas están
sincronizadas (64/64 reglas, 79 reservadas).

```bash
python3 herramientas/chequeo_gramatica.py
```

Contenido por bloques:

| Líneas | Bloque |
|---|---|
| 38–47 | `programa` + `sentencias`: `quihubo` … `chao` con saltos obligatorios |
| 48–104 | `sentencia` y variantes simples: asignación, `guarde`, `devuelva`, `cuenteme`, `describa`, llamada |
| 105–136 | machine learning: `entrene`, opciones y `evalua` |
| 137–151 | estructuras propias: `agregue`/`saque`/`recorra` |
| 152–200 | funciones (`invente`), `fijese_si`/`sino`, `mientras`, `repita`, `pare`/`siga`, `bloque` |
| 201–275 | pipeline `\|>`, operaciones de datos (incluye `prediga`/`clasifique`), `monte`, columnas, etiquetas, `resuma`, tipos |
| 276–303 | visualización `pinte` + cláusulas + `guardela`/`muestrela` |
| 304–438 | expresiones con precedencia (sin `factor`) y `nombre_columna` (acepta reservadas, D5) |
| 440–599 | lexer: 79 reservadas, literales, 23 símbolos, `NL`, comentarios `#`, `ID` Unicode |

Convenciones: reservadas en minúscula sin tildes; `NL` separa
sentencias (con continuación tras `|>`, `,` y operadores); `#`
comenta hasta fin de línea. El código generado vive en `generado/`
(ver su `README.md`) y no se edita a mano.
