# AREPA — Gramática BNF/EBNF (Fases 1–3 + estructuras propias, acumulativa, Linux)

Esta especificación es la fuente formal del lenguaje y se corresponde 1 a 1
con la implementación en ANTLR4 (`gramatica/Arepa.g4`). La sincronía entre
ambos archivos se verifica automáticamente con
`python3 herramientas/chequeo_gramatica.py`, que exige las **57 reglas** del
`.g4`, ningún no terminal inventado y las **65 palabras reservadas**.

**Notación EBNF usada:**

| Símbolo | Significado |
|---|---|
| `::=` | definición |
| `<…>` | no terminal (siempre el nombre de una regla del `.g4`) |
| `"…"` | terminal (literal) |
| `\|` | alternativa |
| `( … )` | agrupación |
| `[ … ]` | opcional (0 o 1 vez) |
| `{ … }` | repetición (0 o más veces) |

Los tokens del lexer se escriben en MAYÚSCULAS sin ángulos (`NL`, `ID`,
`ENTERO`, `EOF`, …) y no son no terminales de la EBNF.

Terminales auxiliares: `NL` = salto de línea (`\r? \n`)+; `ESPACIO` = espacios
y tabuladores (se descartan); `COMENTARIO` = `#` hasta fin de línea (se
descarta). La notación `[NL]` de este documento representa una continuación de
línea opcional; en el `.g4` corresponde a `NL*`.

---

## 1. Programa

```ebnf
<programa>      ::= { NL } "quihubo" NL+ [ <sentencias> ] { NL } "chao" { NL } EOF

<sentencias>    ::= <sentencia> { NL+ <sentencia> }
```

El salto de línea después de `"quihubo"` es obligatorio: ni la apertura ni el
cierre comparten línea con otras sentencias.

## 2. Sentencias

```ebnf
<sentencia>         ::= <asignacion>
                      | <instruccion_guarde>
                      | <instruccion_grafica>
                      | <condicional>
                      | <ciclo_mientras>
                      | <ciclo_repita>
                      | <instruccion_pare>
                      | <instruccion_siga>
                      | <definicion_funcion>
                      | <instruccion_devolver>
                      | <instruccion_cuenteme>
                      | <instruccion_describa>
                      | <instruccion_agregue>
                      | <instruccion_saque>
                      | <ciclo_recorra>
                      | <instruccion_llamada>

<asignacion>        ::= <identificador> { <indice> } "=" <expresion>

<instruccion_guarde>   ::= "guarde" <identificador> "como" <cadena>
<instruccion_devolver> ::= "devuelva" [ <expresion> ]
<instruccion_cuenteme> ::= "cuenteme" [ <lista_argumentos> ]
<instruccion_describa> ::= "describa" <identificador>
<instruccion_llamada>  ::= <llamada_funcion>

<instruccion_agregue> ::= "agregue" [NL] <expresion> [NL] "en" [NL] <identificador>
<instruccion_saque>   ::= "saque" [NL] <expresion> [NL] "de" [NL] <identificador>
<ciclo_recorra>       ::= "recorra" [NL] <identificador> [NL] "en" [NL]
                          <identificador> [NL] <bloque>

<condicional>       ::= "fijese_si" [NL] "(" [NL] <expresion_logica> [NL] ")"
                        [NL] <bloque>
                        [ "sino" [NL] ( <condicional> | <bloque> ) ]

<bloque>            ::= "{" [ NL ] [ <sentencias> ] [ NL ] "}"

<ciclo_mientras>    ::= "mientras" [NL] "(" [NL] <expresion_logica> [NL] ")"
                         [NL] <bloque>

<ciclo_repita>      ::= "repita" [NL] <expresion_logica> [NL] "veces" [NL] <bloque>
                      | "repita" [NL] <identificador> [NL] "desde" [NL]
                        <expresion_logica> [NL] "hasta" [NL] <expresion_logica>
                        [ [NL] "paso" [NL] <expresion_logica> ] [NL] <bloque>

<instruccion_pare>  ::= "pare"
<instruccion_siga>  ::= "siga"

<definicion_funcion> ::= "invente" <identificador> "(" [ <parametros> ] ")" <bloque>

<parametros>        ::= <identificador> { "," [NL] <identificador> }
```

Notas de correspondencia con el `.g4`:

- La asignación admite índices encadenados antes del `=`
  (`v[1] = 10`, `m["a"][2] = 3`), de ahí `{ <indice> }`.
- Las tres alternativas nuevas van en el mismo orden que en el `.g4`, justo
  antes de `<instruccion_llamada>`.
- La alternativa de llamada es la regla envoltorio `<instruccion_llamada>`,
  que solo contiene a `<llamada_funcion>`; se creó para que una expresión
  suelta (por ejemplo `x + 1` sola en una línea) no sea sentencia y las
  cláusulas de `pinte` no se confundan con sentencias nuevas.

## 3. Expresiones y pipeline

```ebnf
<expresion>          ::= <etapa_pipeline> { [NL] "|>" [NL] <etapa_pipeline> }

<etapa_pipeline>     ::= <operacion_datos> | <expresion_logica>

<expresion_logica>   ::= <conjuncion> { "o" [NL] <conjuncion> }
<conjuncion>         ::= <negacion> { "y" [NL] <negacion> }
<negacion>           ::= "no" [NL] <negacion> | <comparacion>

<comparacion>        ::= <aritmetica> [ <operador_relacional> [NL] <aritmetica> ]

<operador_relacional> ::= "==" | "!=" | "<=" | ">=" | "<" | ">"

<aritmetica>         ::= <termino> { ( "+" | "-" ) [NL] <termino> }
<termino>            ::= <unario> { ( "*" | "/" | "%" ) [NL] <unario> }
<unario>             ::= "-" [NL] <unario> | <potencia>
<potencia>           ::= <acceso> [ "^" [NL] <unario> ]
<acceso>             ::= <atomo> { <indice> }

<indice>             ::= "[" [NL] <expresion> [NL] "]"
```

Ya **no existe el no terminal `factor`**: la jerarquía aritmética es
`<aritmetica>` → `<termino>` → `<unario>` → `<potencia>` → `<acceso>` →
`<atomo>`. La potencia se ubica entre el menos unario y el acceso, de modo que
`^` pega más que `-` y asocia a la derecha, mientras que los índices se aplican
al átomo antes que cualquier operador.

```ebnf
<atomo>              ::= ENTERO | DECIMAL | <cadena>
                       | "obvio" | "falso" | "nada"
                       | <lista_literal>
                       | <registro_literal>
                       | <tabla_literal>
                       | <llamada_funcion>
                       | <nombre_columna>
                       | "(" [NL] <expresion> [NL] ")"

<llamada_funcion>    ::= <identificador> "(" [ <lista_argumentos> ] ")"
<lista_argumentos>   ::= <expresion> { "," [NL] <expresion> }

<cadena>             ::= CADENA

<identificador>      ::= ID
<nombre_columna>     ::= ID | PALABRA_RESERVADA
```

`nombre_columna` acepta además cualquier palabra reservada (las 65 de la
sección 7): los nombres de las columnas provienen de archivos externos y
pueden coincidir con el vocabulario del lenguaje (decisión D5 del catálogo).
Las variables declaradas por el programa sí exigen `ID` puro.

## 4. Literales de estructuras propias

Listas, registros y tablas se construyen en memoria con literales. Los
corchetes delimitan listas y filas; las llaves, registros.

```ebnf
<lista_literal>      ::= "[" [NL] [ <expresion> { "," [NL] <expresion> } ] [NL] "]"

<registro_literal>   ::= "{" [NL] [ <par_registro> { "," [NL] <par_registro> } ] [NL] "}"
<par_registro>       ::= <clave_registro> ":" [NL] <expresion>
<clave_registro>     ::= <nombre_columna> | <cadena>

<tabla_literal>      ::= "arme" [NL] <lista_columnas>
                         [ [NL] "con" [NL] "[" [NL]
                           [ <fila_literal> { "," [NL] <fila_literal> } ] [NL] "]" ]

<fila_literal>       ::= "[" [NL] [ <expresion> { "," [NL] <expresion> } ] [NL] "]"
```

- `[]` es la lista vacía y `{}` el registro vacío; ambos literales son válidos.
- La tabla puede declararse sin filas (`arme [a, b]`) y llenarse después con
  `agregue`, o construirse completa con la cláusula `con`.
- `clave_registro` admite nombres de columna (incluidas palabras reservadas)
  o cadenas, pero no expresiones arbitrarias.

## 5. Operaciones sobre datos

```ebnf
<operacion_datos>    ::= <instruccion_monte>
                       | "escoja" <lista_columnas>
                       | "deje" "donde" <expresion_logica>
                       | "acomode" [ "por" ] <lista_columnas> [ <direccion> ]
                       | "cree" <nombre_columna> "=" <expresion_logica>
                       | "renombre" <nombre_columna> "->" <nombre_columna>
                       | "limpie" ( "duplicados" | "vacios" ) [ "con" <expresion_logica> ]
                       | "convierta" <nombre_columna> "->" <tipo_dato>
                       | "junte" "por" <lista_columnas>
                       | "resuma" [NL] <item_resumen> { "," [NL] <item_resumen> }

<instruccion_monte>  ::= "monte" <cadena> [ <opciones_archivo> ]

<opciones_archivo>   ::= "con" [NL] <opcion_archivo> { "," [NL] <opcion_archivo> }
<opcion_archivo>     ::= "encabezado" [ ( "obvio" | "falso" ) ] | "separador" [NL] <cadena>
<direccion>          ::= "pa_arriba" | "pa_abajo"
<lista_columnas>     ::= "[" [NL] <nombre_columna> { "," [NL] <nombre_columna> } [NL] "]"
<item_resumen>       ::= <nombre_columna> "=" <llamada_funcion>
<tipo_dato>          ::= "numero" | "texto" | "logico" | "fecha"
```

## 6. Visualización

```ebnf
<instruccion_grafica> ::= "pinte" <tipo_grafica> <identificador>
                          { [NL] <clausula_estetica> }
                          [ [NL] <final_grafica> ]

<final_grafica>       ::= "guardela" [NL] <cadena> | "muestrela"

<tipo_grafica>        ::= "barras" | "lineas" | "histograma" | "dispersion" | "cajas"

<clausula_estetica>   ::= "titulo"  [NL] <cadena>
                        | "ejex"    [NL] <nombre_columna>
                        | "ejey"    [NL] ( <nombre_columna> | <lista_literal> )
                        | "leyenda" [NL] <cadena>
```

`ejey` admite **una columna** o una **lista de columnas** (varias series). En el
`.g4` la producción es `EJEY NL* (nombre_columna | lista_literal)` y `ejex`
sigue admitiendo una sola columna.

## 7. Precedencia y asociatividad

De menor a mayor prioridad:

| Nivel | Regla | Operadores | Asociatividad |
|---|---|---|---|
| 1 | `<expresion>` | `\|>` | izquierda |
| 2 | `<expresion_logica>` | `o` | izquierda |
| 3 | `<conjuncion>` | `y` | izquierda |
| 4 | `<negacion>` | `no` (prefijo) | derecha |
| 5 | `<comparacion>` | `==` `!=` `<=` `>=` `<` `>` | no asociativa (máx. 1) |
| 6 | `<aritmetica>` | `+` `-` | izquierda |
| 7 | `<termino>` | `*` `/` `%` | izquierda |
| 8 | `<unario>` | `-` (prefijo) | derecha |
| 9 | `<potencia>` | `^` | derecha |
| 10 | `<acceso>` / `<indice>` | `[ … ]` | izquierda |
| 11 | `<atomo>` | literales, llamadas, paréntesis | — |

Consecuencias verificables:

- `-2 ^ 2` = `-(2 ^ 2)` = **-4**, porque `^` (nivel 9) pega más que el menos
  unario (nivel 8).
- `2 ^ 3 ^ 2` = `2 ^ (3 ^ 2)` = **512**, porque `^` asocia a la derecha
  (`<potencia> ::= <acceso> [ "^" [NL] <unario> ]`).
- `2 ^ -3` es válido: el operando derecho de `^` es un `<unario>`, que admite
  el menos prefijo.
- `-2 * 3` = `(-2) * 3` = **-6**, y `2 * 3 ^ 2` = `2 * 9` = **18**.
- `a[0] + 1` indexa antes de sumar, y `no a == b` es `no (a == b)` porque la
  comparación tiene más prioridad que la negación.

## 8. Léxico

```ebnf
ENTERO     ::= DÍGITO { DÍGITO }
DECIMAL    ::= DÍGITO { DÍGITO } "." DÍGITO { DÍGITO }
CADENA     ::= '"' { ESCAPE | CARACTER } '"'        donde CARACTER ≠ '"' '\' CR LF
ESCAPE     ::= "\" ( "b" | "t" | "n" | "r" | '"' | "\" )
COMENTARIO ::= "#" { CARACTER } FIN_DE_LÍNEA        (descartado)
ESPACIO    ::= " " | TAB | FF                        (descartado)
```

### 8.1 Palabras reservadas (65)

Se agrupan por tema, en el mismo orden en que las declara el lexer.

```ebnf
PALABRA_RESERVADA ::= "quihubo" | "chao"
                    | "monte" | "guarde" | "como" | "con" | "encabezado"
                    | "separador"
                    | "escoja" | "deje" | "donde" | "acomode" | "por"
                    | "pa_arriba" | "pa_abajo" | "cree" | "renombre"
                    | "limpie" | "duplicados" | "vacios" | "convierta"
                    | "junte" | "resuma"
                    | "arme" | "agregue" | "saque" | "recorra" | "en" | "de"
                    | "numero" | "texto" | "logico" | "fecha"
                    | "pinte" | "barras" | "lineas" | "histograma"
                    | "dispersion" | "cajas" | "titulo" | "ejex" | "ejey"
                    | "leyenda" | "guardela" | "muestrela"
                    | "invente" | "devuelva" | "fijese_si" | "sino"
                    | "cuenteme" | "describa"
                    | "mientras" | "repita" | "veces" | "desde" | "hasta"
                    | "paso" | "pare" | "siga"
                    | "obvio" | "falso" | "nada"
                    | "y" | "o" | "no"
```

Son 65 palabras reservadas en total: 2 de estructura del programa, 6 de carga
y almacenamiento, 13 de selección y preparación, 2 de transformación, 6 de
estructuras propias, 4 de tipos, 12 de visualización, 6 de abstracción y
control, 8 de ciclos, 3 literales especiales y 3 operadores lógicos. Los
comentarios pueden aparecer en cualquier línea del programa.

### 8.2 Símbolos y operadores

Tokens de una sola pieza (no son palabras reservadas):

| Token | Texto | Token | Texto | Token | Texto |
|---|---|---|---|---|---|
| `PIPE` | `\|>` | `IGUAL_IGUAL` | `==` | `MAS` | `+` |
| `FLECHA` | `->` | `DIFERENTE` | `!=` | `MENOS` | `-` |
| `ASIGNACION` | `=` | `MENOR_IGUAL` | `<=` | `POR_OP` | `*` |
| `PAREN_I` / `PAREN_D` | `(` / `)` | `MAYOR_IGUAL` | `>=` | `DIVISION` | `/` |
| `CORCHETE_I` / `CORCHETE_D` | `[` / `]` | `MENOR` | `<` | `MODULO` | `%` |
| `LLAVE_I` / `LLAVE_D` | `{` / `}` | `MAYOR` | `>` | `POTENCIA` | `^` |
| `COMA` | `,` | `DOS_PUNTOS` | `:` | `NL` | salto de línea |

### 8.3 Identificadores

En el `.g4` la regla es `ID : [\p{L}_] [\p{L}\p{N}_]*`, es decir, una letra
Unicode (incluye ñ y tildes) o guion bajo al inicio, y después letras, dígitos
Unicode o guion bajo. En esta EBNF eso equivale a:

```ebnf
<identificador> ::= LETRA_UNICODE | "_" , { LETRA_UNICODE | DÍGITO_UNICODE | "_" }
```

Precedencia léxica: las palabras reservadas se listan antes que la regla de
identificadores; `DECIMAL` antes que `ENTERO`; `|>` y `->` antes que los
símbolos simples.

## 9. Correspondencia con ANTLR4

La regla EBNF `{ X }` equivale a la estrella ANTLR `X*`; `[ X ]` equivale a
`X?`; `[NL]` documenta un `NL*` opcional de continuación de línea. Los nombres
de las 57 reglas coinciden exactamente con los del `.g4`, en el mismo orden:

`programa`, `sentencias`, `sentencia`, `instruccion_llamada`, `asignacion`,
`instruccion_guarde`, `instruccion_devolver`, `instruccion_cuenteme`,
`instruccion_describa`, `instruccion_agregue`, `instruccion_saque`,
`ciclo_recorra`, `definicion_funcion`, `parametros`, `condicional`,
`ciclo_mientras`, `ciclo_repita`, `instruccion_pare`, `instruccion_siga`,
`bloque`, `expresion`, `etapa_pipeline`, `operacion_datos`,
`instruccion_monte`, `opciones_archivo`, `opcion_archivo`, `direccion`,
`lista_columnas`, `item_resumen`, `tipo_dato`, `instruccion_grafica`,
`tipo_grafica`, `clausula_estetica`, `final_grafica`, `expresion_logica`,
`conjuncion`, `negacion`, `comparacion`, `operador_relacional`, `aritmetica`,
`termino`, `unario`, `potencia`, `acceso`, `indice`, `atomo`, `lista_literal`,
`registro_literal`, `par_registro`, `clave_registro`, `tabla_literal`,
`fila_literal`, `llamada_funcion`, `lista_argumentos`, `cadena`,
`identificador`, `nombre_columna`.

Para regenerar el front-end:

```bash
antlr4 -Dlanguage=Python3 -visitor -no-listener gramatica/Arepa.g4
```

Y para comprobar que este documento sigue sincronizado con la gramática:

```bash
python3 herramientas/chequeo_gramatica.py
# Sincronizado: 57/57 reglas y 65 reservadas.
```
