# Código generado por ANTLR (no editar a mano)

Lexer, parser y Visitor de Python generados desde la fuente única
`gramatica/Arepa.g4` con ANTLR 4.13.2. Es la **única** parte del
proyecto que no es código propio (herramienta exigida por el curso).

| Archivo | Qué es |
|---|---|
| `ArepaLexer.py` | lexer generado (59 reservadas, operadores, literales) |
| `ArepaParser.py` | parser generado (46 reglas) |
| `ArepaVisitor.py` | Visitor base que extienden `EjecutorArepa` y `EvaluadorExpresiones` |
| `Arepa.tokens` / `ArepaLexer.tokens` | tablas de tokens |
| `Arepa.interp` / `ArepaLexer.interp` | datos intermedios de ANTLR |

Regenerar en Linux (requiere Java 11+ y el jar 4.13.2):

```bash
chmod +x generar_gramatica.sh
./generar_gramatica.sh
```

Sincronía verificable EBNF ↔ `.g4` (46/46 reglas, 59 reservadas):

```bash
python3 herramientas/chequeo_gramatica.py
```

Tras regenerar, correr `python3 pruebas/test_proyecto.py` (194 pruebas).
