/*
 * ============================================================================
 *  AREPA - Análisis Reproducible de datos Escrito con Palabras Autóctonas
 * ============================================================================
 *  Gramática léxica y sintáctica (Fase 1: Especificación y front-end)
 *  Curso: Lenguajes de Programación y Transducción
 *  Universidad Sergio Arboleda - Semestre 2026-2
 *
 *  AREPA es un DSL para ciencia de datos y visualización cuyo vocabulario
 *  está tomado del español hablado en Colombia. Los programas usan la
 *  extensión .arepa y comienzan con "quihubo" y terminan con "chao".
 *
 *  Convenciones de diseño:
 *   - Las palabras reservadas se escriben en minúscula, sin tildes.
 *   - El salto de línea (NL) separa sentencias; se permite continuación
 *     de línea después de "|>", ",", operadores binarios y dentro de
 *     paréntesis, corchetes.
 *   - Los comentarios inician con "#" y llegan al final de la línea.
 *
 *  Para generar el front-end en Python:
 *    antlr4 -Dlanguage=Python3 -visitor -no-listener Arepa.g4
 * ============================================================================
 */

grammar Arepa;

// ============================================================================
// 1. REGLAS SINTÁCTICAS (PARSER)
// ============================================================================

// --- Programa ---------------------------------------------------------------

programa
    : NL* QUIHUBO NL* sentencias? NL* CHAO NL* EOF
    ;

sentencias
    : sentencia (NL+ sentencia)*
    ;

// --- Sentencias -------------------------------------------------------------

sentencia
    : asignacion
    | instruccion_guarde
    | instruccion_grafica
    | condicional
    | definicion_funcion
    | instruccion_devolver
    | instruccion_cuenteme
    | instruccion_describa
    | instruccion_llamada
    ;

// Una llamada a función puede aparecer como sentencia propia.
// Las demás expresiones sueltas no son sentencias: así se evita que una
// palabra reservada al inicio de línea se confunda con el inicio de una
// nueva instrucción (p. ej. las cláusulas de "pinte").
instruccion_llamada
    : llamada_funcion
    ;

asignacion
    : identificador ASIGNACION expresion
    ;

instruccion_guarde
    : GUARDE identificador COMO cadena
    ;

instruccion_devolver
    : DEVUELVA expresion?
    ;

instruccion_cuenteme
    : CUENTEME lista_argumentos?
    ;

instruccion_describa
    : DESCRIBA identificador
    ;

// --- Funciones --------------------------------------------------------------
// "invente" declara una función: invente nombre(parametros) { ... }

definicion_funcion
    : INVENTE identificador PAREN_I parametros? PAREN_D bloque
    ;

parametros
    : identificador (COMA NL* identificador)*
    ;

// --- Condicionales ----------------------------------------------------------
// "fijese si" evalúa una condición; "sino" es el camino alterno.

condicional
    : FIJESE_SI NL* PAREN_I NL* expresion_logica NL* PAREN_D NL* bloque
      (SINO NL* (condicional | bloque))?
    ;

bloque
    : LLAVE_I NL* sentencias? NL* LLAVE_D
    ;

// --- Expresiones y pipelines ------------------------------------------------
// Una expresión general es un encadenamiento (pipeline) de etapas separadas
// por "|>". Cada etapa puede ser una operación sobre tablas o una expresión
// booleana/aritmética convencional.

expresion
    : etapa_pipeline (NL* PIPE NL* etapa_pipeline)*
    ;

etapa_pipeline
    : operacion_datos
    | expresion_logica
    ;

// --- Operaciones sobre conjuntos de datos -----------------------------------

operacion_datos
    : instruccion_monte
    | ESCOJA lista_columnas
    | DEJE DONDE expresion_logica
    | ACOMODE POR? lista_columnas direccion?
    | CREE nombre_columna ASIGNACION expresion_logica
    | RENOMBRE nombre_columna FLECHA nombre_columna
    | LIMPIE (DUPLICADOS | VACIOS) (CON expresion_logica)?
    | CONVIERTA nombre_columna FLECHA tipo_dato
    | JUNTE POR lista_columnas
    | RESUMA NL* item_resumen (COMA NL* item_resumen)*
    ;

instruccion_monte
    : MONTE cadena opciones_archivo?
    ;

opciones_archivo
    : CON NL* opcion_archivo (COMA NL* opcion_archivo)*
    ;

opcion_archivo
    : ENCABEZADO (OBVIO | FALSO)?
    | SEPARADOR NL* cadena
    ;

direccion
    : PA_ARRIBA
    | PA_ABAJO
    ;

lista_columnas
    : CORCHETE_I NL* nombre_columna (COMA NL* nombre_columna)* NL* CORCHETE_D
    ;

item_resumen
    : nombre_columna ASIGNACION llamada_funcion
    ;

tipo_dato
    : NUMERO
    | TEXTO
    | LOGICO
    | FECHA
    ;

// --- Instrucciones de visualización -----------------------------------------
// "pinte <tipo> <tabla>" reconoce la intención gráfica. Las cláusulas de
// estética son opcionales y pueden ir en cualquier orden.

instruccion_grafica
    : PINTE tipo_grafica identificador (NL* clausula_estetica)*
      (NL* final_grafica)?
    ;

tipo_grafica
    : BARRAS
    | LINEAS
    | HISTOGRAMA
    | DISPERSION
    | CAJAS
    ;

clausula_estetica
    : TITULO NL* cadena
    | EJEX NL* nombre_columna
    | EJEY NL* nombre_columna
    | LEYENDA NL* cadena
    ;

final_grafica
    : GUARDELA NL* cadena
    | MUESTRELA
    ;

// --- Jerarquía de expresiones booleanas y aritméticas -----------------------
// Precedencia (de menor a mayor): o < y < no < comparación < +- < */% < ^

expresion_logica
    : conjuncion (O NL* conjuncion)*
    ;

conjuncion
    : negacion (Y NL* negacion)*
    ;

negacion
    : NO NL* negacion
    | comparacion
    ;

comparacion
    : aritmetica (operador_relacional NL* aritmetica)?
    ;

operador_relacional
    : IGUAL_IGUAL
    | DIFERENTE
    | MENOR_IGUAL
    | MAYOR_IGUAL
    | MENOR
    | MAYOR
    ;

aritmetica
    : termino ((MAS | MENOS) NL* termino)*
    ;

termino
    : factor ((POR_OP | DIVISION | MODULO) NL* factor)*
    ;

factor
    : unario (POTENCIA NL* factor)?
    ;

unario
    : MENOS NL* unario
    | atomo
    ;

atomo
    : ENTERO
    | DECIMAL
    | cadena
    | OBVIO
    | FALSO
    | NADA
    | llamada_funcion
    | nombre_columna
    | PAREN_I NL* expresion NL* PAREN_D
    ;

llamada_funcion
    : identificador PAREN_I lista_argumentos? PAREN_D
    ;

lista_argumentos
    : expresion (COMA NL* expresion)*
    ;

cadena
    : CADENA
    ;

identificador
    : ID
    ;

// Los nombres de las columnas provienen de los archivos externos, de modo
// que el lenguaje no puede evitar que coincidan con una palabra reservada
// (por ejemplo una columna "fecha"). En todas las posiciones donde se
// referencia una columna se acepta un identificador o cualquier palabra
// reservada. Las variables declaradas en el programa sí exigen ID puro.

nombre_columna
    : ID
    | QUIHUBO | CHAO | MONTE | GUARDE | COMO | CON | ENCABEZADO | SEPARADOR
    | ESCOJA | DEJE | DONDE | ACOMODE | POR | PA_ARRIBA | PA_ABAJO | CREE
    | RENOMBRE | LIMPIE | DUPLICADOS | VACIOS | CONVIERTA | JUNTE | RESUMA
    | NUMERO | TEXTO | LOGICO | FECHA
    | PINTE | BARRAS | LINEAS | HISTOGRAMA | DISPERSION | CAJAS | TITULO
    | EJEX | EJEY | LEYENDA | GUARDELA | MUESTRELA
    | INVENTE | DEVUELVA | FIJESE_SI | SINO | CUENTEME | DESCRIBA
    | OBVIO | FALSO | NADA | Y | O | NO
    ;

// ============================================================================
// 2. REGLAS LÉXICAS (LEXER)
// ============================================================================

// --- Estructura del programa ------------------------------------------------

QUIHUBO    : 'quihubo' ;     // abre el programa
CHAO       : 'chao' ;        // cierra el programa

// --- Carga y almacenamiento --------------------------------------------------

MONTE      : 'monte' ;       // carga un CSV
GUARDE     : 'guarde' ;      // guarda una tabla en CSV
COMO       : 'como' ;
CON        : 'con' ;
ENCABEZADO : 'encabezado' ;
SEPARADOR  : 'separador' ;

// --- Selección y preparación --------------------------------------------------

ESCOJA     : 'escoja' ;      // selecciona columnas
DEJE       : 'deje' ;        // deja (filtra) las filas que cumplen
DONDE      : 'donde' ;
ACOMODE    : 'acomode' ;     // ordena
POR        : 'por' ;
PA_ARRIBA  : 'pa_arriba' ;   // ascendente
PA_ABAJO   : 'pa_abajo' ;    // descendente
CREE       : 'cree' ;        // crea columna calculada
RENOMBRE   : 'renombre' ;    // renombra columna
LIMPIE     : 'limpie' ;      // limpia duplicados o vacíos
DUPLICADOS : 'duplicados' ;
VACIOS     : 'vacios' ;
CONVIERTA  : 'convierta' ;   // convierte tipos

// --- Transformación y análisis -------------------------------------------------

JUNTE      : 'junte' ;       // agrupa
RESUMA     : 'resuma' ;      // agrega/resume

// --- Tipos ---------------------------------------------------------------------

NUMERO     : 'numero' ;
TEXTO      : 'texto' ;
LOGICO     : 'logico' ;
FECHA      : 'fecha' ;

// --- Visualización ----------------------------------------------------------------

PINTE      : 'pinte' ;       // produce una gráfica
BARRAS     : 'barras' ;
LINEAS     : 'lineas' ;
HISTOGRAMA : 'histograma' ;
DISPERSION : 'dispersion' ;
CAJAS      : 'cajas' ;
TITULO     : 'titulo' ;
EJEX       : 'ejex' ;
EJEY       : 'ejey' ;
LEYENDA    : 'leyenda' ;
GUARDELA   : 'guardela' ;    // exporta la gráfica a PNG
MUESTRELA  : 'muestrela' ;   // muestra la gráfica en pantalla

// --- Abstracción y control ------------------------------------------------------

INVENTE    : 'invente' ;     // define una función
DEVUELVA   : 'devuelva' ;    // retorna un valor
FIJESE_SI  : 'fijese_si' ;   // condicional
SINO       : 'sino' ;
CUENTEME   : 'cuenteme' ;    // imprime/muestra valores
DESCRIBA   : 'describa' ;    // resumen estadístico de una tabla

// --- Literales especiales ---------------------------------------------------------

OBVIO      : 'obvio' ;       // verdadero
FALSO      : 'falso' ;
NADA       : 'nada' ;        // valor faltante / nulo

// --- Operadores lógicos ------------------------------------------------------------

Y          : 'y' ;
O          : 'o' ;
NO         : 'no' ;

// --- Literales compuestos ------------------------------------------------------------

DECIMAL    : [0-9]+ '.' [0-9]+ ;
ENTERO     : [0-9]+ ;
CADENA     : '"' ( '\\' [btnr"\\] | ~["\\\r\n] )* '"' ;

// --- Símbolos y operadores -------------------------------------------------------------

PIPE       : '|>' ;          // encadenamiento de operaciones
FLECHA     : '->' ;          // renombre / conversión
ASIGNACION : '=' ;
IGUAL_IGUAL: '==' ;
DIFERENTE  : '!=' ;
MENOR_IGUAL: '<=' ;
MAYOR_IGUAL: '>=' ;
MENOR      : '<' ;
MAYOR      : '>' ;
MAS        : '+' ;
MENOS      : '-' ;
POR_OP     : '*' ;
DIVISION   : '/' ;
MODULO     : '%' ;
POTENCIA   : '^' ;
PAREN_I    : '(' ;
PAREN_D    : ')' ;
CORCHETE_I : '[' ;
CORCHETE_D : ']' ;
LLAVE_I    : '{' ;
LLAVE_D    : '}' ;
COMA       : ',' ;

// --- Estructura del texto fuente -------------------------------------------------------

NL         : ('\r'? '\n')+ ;            // salto de línea: separa sentencias
WS         : [ \t\u000C]+ -> skip ;     // espacios en blanco
COMENTARIO : '#' ~[\r\n]* -> skip ;     // comentario hasta fin de línea

// --- Identificadores (permiten ñ, tildes y letras Unicode) -----------------------------

ID         : [\p{L}_] [\p{L}\p{N}_]* ;
