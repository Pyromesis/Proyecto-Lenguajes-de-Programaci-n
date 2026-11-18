# Gramática de AREPA

`Arepa.g4` es la **fuente única** del lenguaje: gramática combinada
lexer+parser para ANTLR 4.13.2 (Fases 1–3). La especificación formal
equivalente está en `docs/03_gramatica_ebnf.md`; ambas están
sincronizadas (64/64 reglas, 79 reservadas).

```bash
python3 herramientas/chequeo_gramatica.py
```

Contenido por bloques:

- `programa` y `sentencias`: estructura `quihubo` … `chao`.
- `sentencia`: asignación, exportación, retorno, impresión y llamadas.
- Aprendizaje automático: `entrene`, opciones y `evalua`.
- Estructuras: `agregue`, `saque` y `recorra`.
- Funciones, condicionales, ciclos y bloques.
- Pipelines `|>`: carga, operaciones de datos, predicción y clasificación.
- Visualización: `pinte`, sus cláusulas, `guardela` y `muestrela`.
- Expresiones con precedencia y nombres de columna.
- Lexer: reservadas, literales, símbolos, saltos de línea, comentarios e identificadores Unicode.

Convenciones: reservadas en minúscula sin tildes; `NL` separa
sentencias (con continuación tras `|>`, `,` y operadores); `#`
comenta hasta fin de línea. El código generado vive en `generado/`
(consulte la [guía de regeneración](../generado/README.md)) y no se edita a mano.
