# AREPA — Gramática BNF/EBNF (Fase 1)

Esta especificación es la fuente formal del lenguaje y se corresponde 1 a 1
con la implementación en ANTLR4 (`gramatica/Arepa.g4`).

**Notación EBNF usada:**

| Símbolo | Significado |
|---|---|
| `::=` | definición |
| `<…>` | no terminal |
| `"…"` | terminal (literal) |
| `\|` | alternativa |
| `( … )` | agrupación |
| `[ … ]` | opcional (0 o 1 vez) |
| `{ … }` | repetición (0 o más veces) |

Terminales auxiliares: `NL` = salto de línea (`\r? \n`)+; `ESPACIO` = espacios
y tabuladores (se descartan); `COMENTARIO` = `#` hasta fin de línea (se descarta).

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
                      | "guarde" <identificador> "como" <cadena>
                      | <instruccion_grafica>
                      | <condicional>
                      | <definicion_funcion>
                      | "devuelva" [ <expresion> ]
                      | "cuenteme" [ <lista_argumentos> ]
                      | "describa" <identificador>
                      | <llamada_funcion>

<asignacion>        ::= <identificador> "=" <expresion>

<condicional>       ::= "fijese_si" [NL] "(" [NL] <expresion_logica> [NL] ")"
                        [NL] <bloque>
                        [ "sino" [NL] ( <condicional> | <bloque> ) ]

<bloque>            ::= "{" [ NL ] [ <sentencias> ] [ NL ] "}"

<definicion_funcion> ::= "invente" <identificador> "(" [ <parametros> ] ")" <bloque>

<parametros>        ::= <identificador> { "," [NL] <identificador> }
```

## 3. Expresiones y pipeline

```ebnf
<expresion>          ::= <etapa_pipeline> { [NL] "|>" [NL] <etapa_pipeline> }

<etapa_pipeline>     ::= <operacion_datos> | <expresion_logica>

<expresion_logica>   ::= <conjuncion> { "o" [NL] <conjuncion> }
<conjuncion>         ::= <negacion> { "y" [NL] <negacion> }
<negacion>           ::= "no" [NL] <negacion> | <comparacion>

<comparacion>        ::= <aritmetica> [ ( "==" | "!=" | "<=" | ">=" | "<" | ">" ) [NL] <aritmetica> ]

<aritmetica>         ::= <termino> { ( "+" | "-" ) [NL] <termino> }
<termino>            ::= <factor> { ( "*" | "/" | "%" ) [NL] <factor> }
<factor>             ::= <unario> [ "^" [NL] <factor> ]
<unario>             ::= "-" [NL] <unario> | <atomo>

<atomo>              ::= ENTERO | DECIMAL | <cadena>
                       | "obvio" | "falso" | "nada"
                       | <llamada_funcion>
                       | <nombre_columna>
                       | "(" [NL] <expresion> [NL] ")"

<llamada_funcion>    ::= <identificador> "(" [ <lista_argumentos> ] ")"
<lista_argumentos>   ::= <expresion> { "," [NL] <expresion> }

<identificador>      ::= LETRA { LETRA | DÍGITO | "_" }
<nombre_columna>     ::= <identificador> | PALABRA_RESERVADA
```

`nombre_columna` acepta además cualquier palabra reservada (las 51 de la
sección 6): los nombres de las columnas provienen de archivos externos y
pueden coincidir con el vocabulario del lenguaje (decisión D5 del catálogo).

## 4. Operaciones sobre datos

```ebnf
<operacion_datos>    ::= "monte" <cadena> [ <opciones_archivo> ]
                       | "escoja" <lista_columnas>
                       | "deje" "donde" <expresion_logica>
                       | "acomode" [ "por" ] <lista_columnas> [ <direccion> ]
                       | "cree" <nombre_columna> "=" <expresion_logica>
                       | "renombre" <nombre_columna> "->" <nombre_columna>
                       | "limpie" ( "duplicados" | "vacios" ) [ "con" <expresion_logica> ]
                       | "convierta" <nombre_columna> "->" <tipo_dato>
                       | "junte" "por" <lista_columnas>
                       | "resuma" [NL] <item_resumen> { "," [NL] <item_resumen> }

<opciones_archivo>   ::= "con" [NL] <opcion_archivo> { "," [NL] <opcion_archivo> }
<opcion_archivo>     ::= "encabezado" [ ( "obvio" | "falso" ) ] | "separador" [NL] <cadena>
<direccion>          ::= "pa_arriba" | "pa_abajo"
<lista_columnas>     ::= "[" [NL] <nombre_columna> { "," [NL] <nombre_columna> } [NL] "]"
<item_resumen>       ::= <nombre_columna> "=" <llamada_funcion>
<tipo_dato>          ::= "numero" | "texto" | "logico" | "fecha"
```

## 5. Visualización

```ebnf
<instruccion_grafica> ::= "pinte" <tipo_grafica> <identificador>
                          { [NL] <clausula_estetica> }
                          [ [NL] ( "guardela" [NL] <cadena> | "muestrela" ) ]

<tipo_grafica>        ::= "barras" | "lineas" | "histograma" | "dispersion" | "cajas"

<clausula_estetica>   ::= "titulo"  [NL] <cadena>
                        | "ejex"    [NL] <nombre_columna>
                        | "ejey"    [NL] <nombre_columna>
                        | "leyenda" [NL] <cadena>
```

## 6. Léxico

```ebnf
ENTERO     ::= DÍGITO { DÍGITO }
DECIMAL    ::= DÍGITO { DÍGITO } "." DÍGITO { DÍGITO }
CADENA     ::= '"' { ESCAPE | CARACTER } '"'        donde CARACTER ≠ '"' '\' CR LF
ESCAPE     ::= "\" ( "b" | "t" | "n" | "r" | '"' | "\" )
COMENTARIO ::= "#" { CARACTER } FIN_DE_LÍNEA        (descartado)
ESPACIO    ::= " " | TAB | FF                        (descartado)

PALABRA_RESERVADA ::= "quihubo" | "chao" | "monte" | "guarde" | "como" | "con"
                    | "encabezado" | "separador" | "escoja" | "deje" | "donde"
                    | "acomode" | "por" | "pa_arriba" | "pa_abajo" | "cree"
                    | "renombre" | "limpie" | "duplicados" | "vacios"
                    | "convierta" | "junte" | "resuma" | "numero" | "texto"
                    | "logico" | "fecha" | "pinte" | "barras" | "lineas"
                    | "histograma" | "dispersion" | "cajas" | "titulo" | "ejex"
                    | "ejey" | "leyenda" | "guardela" | "muestrela" | "invente"
                    | "devuelva" | "fijese_si" | "sino" | "cuenteme" | "describa"
                    | "obvio" | "falso" | "nada" | "y" | "o" | "no"
```

Son 51 palabras reservadas en total. Los comentarios pueden aparecer en
cualquier línea del programa.

Precedencia léxica: las palabras reservadas se listan antes que la regla de
identificadores; `DECIMAL` antes que `ENTERO`; `|>` y `->` antes que los
símbolos simples.

## 7. Correspondencia con ANTLR4

La regla EBNF `{ X }` equivale a la estrella ANTLR `X*`; `[ X ]` equivale a
`X?`. Los nombres de reglas coinciden: `programa`, `sentencias`, `sentencia`,
`asignacion`, `expresion`, `etapa_pipeline`, `operacion_datos`,
`instruccion_grafica`, `condicional`, `definicion_funcion`, etc.
