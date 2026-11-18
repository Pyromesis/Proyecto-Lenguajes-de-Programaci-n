# AREPA — Manual técnico

Guía para mantener y ampliar el intérprete. La
[arquitectura](../05_arquitectura.md) describe los algoritmos y su trazabilidad;
las [reglas semánticas](../09_reglas_semanticas.md) definen el comportamiento
del lenguaje. El [manual de usuario](usuario.md) explica la ejecución.

## Módulos y responsabilidades

| Ruta | Responsabilidad |
|---|---|
| `gramatica/Arepa.g4` | Gramática combinada de lexer y parser |
| `generado/` | Artefactos de ANTLR; se regeneran, no se editan manualmente |
| `src/lenguaje/` | Análisis, traducción de diagnósticos e impresión del árbol |
| `src/datos/` | Tipos, tablas, listas, registros y lectura/escritura CSV |
| `src/expresiones/` | Operadores y evaluación de expresiones |
| `src/runtime/` | Visitor, ámbitos y contexto de ejecución |
| `src/ml/` | Preprocesamiento, modelos y métricas |
| `src/graficas/` | Escalas, dibujos y codificación PNG |
| `src/utiles/` | Conversión de enteros extensos y SHA-256 |
| `src/cli/` | Línea de comandos y consola interactiva |

La dependencia externa de ejecución es `antlr4-python3-runtime==4.13.2`.
La lógica de datos, modelos y gráficas se implementa en el repositorio.

## Generación y ejecución

La generación transforma `Arepa.g4` en los artefactos de `generado/`. Requiere
Java 11 o posterior y ANTLR 4.13.2. La ejecución usa esos artefactos con el
runtime de Python y no requiere Java.

Para regenerar y comprobar la equivalencia con la EBNF:

```bash
bash generar_gramatica.sh
python herramientas/chequeo_gramatica.py
```

La [guía de gramática](../../gramatica/README.md) detalla la configuración.
El verificador compara alternativas, secuencias, opcionales, repeticiones y
terminales de las 64 reglas, además de las 79 palabras reservadas.

## Recorrido del programa

1. `analizar` crea el lexer y el parser e instala el listener de errores.
2. La CLI comprueba los diagnósticos antes de iniciar la ejecución.
3. `EjecutorArepa` recorre el árbol y conserva un `ContextoEjecucion`.
4. `EvaluadorExpresiones` calcula las expresiones según la precedencia del
   árbol y delega las operaciones que requieren el ejecutor.
5. El contexto registra la salida, las tablas, los avisos y los archivos
   generados; la CLI presenta esos resultados.

El Visitor distribuye las operaciones entre estos módulos:

| Módulo en `src/runtime/` | Operaciones |
|---|---|
| `ejecutor.py` | Estado compartido, coordinación y entrada al Visitor |
| `ejecucion_datos.py` | Pipelines, agregaciones y archivos CSV |
| `ejecucion_graficas.py` | Preparación y exportación de gráficas |
| `ejecucion_control.py` | Funciones, condicionales y ciclos |
| `ejecucion_estructuras.py` | Listas, registros, acceso y funciones incorporadas |
| `ejecucion_modelos.py` | Entrenamiento, predicción, clasificación y evaluación |

## Ámbitos y errores

`TablaSimbolos` encadena los ámbitos hijo y padre. Una asignación actualiza
el nombre visible o lo declara si todavía no existe. Solo las funciones
crean un ámbito; los condicionales y ciclos conservan el ámbito actual.
`FuncionArepa` guarda el cuerpo y el entorno de definición para permitir
closures y recursión.

Los errores de dominio derivan de `ErrorArepa` y conservan mensaje, línea,
columna y contexto. La CLI añade la fuente, el indicador de ubicación y una
ayuda de corrección. Las líneas empiezan en 1 y las columnas en 0. En CSV
se distingue la posición del programa de la línea del archivo de datos.

`RetornoFuncion`, `SalirCiclo` y `SeguirCiclo` son señales internas de
control. Se convierten en error semántico únicamente cuando escapan de su
contexto válido. Los avisos aritméticos se registran por separado de la
salida de `cuenteme`.

La CLI devuelve 0 si el programa es válido, incluso con avisos; 1 ante
errores del programa y 2 ante problemas de argumentos o lectura de la fuente.

## Ampliar el lenguaje

Para añadir una instrucción:

1. Modifique `gramatica/Arepa.g4` y enlace la regla desde `sentencia` o
   `operacion_datos`. Declare los tokens reservados antes de los identificadores.
2. Actualice la producción equivalente y las palabras reservadas de
   [la EBNF](../03_gramatica_ebnf.md), regenere y compruebe la sincronización.
3. Implemente `visit<Regla>` en el módulo de ejecución correspondiente, o
   en el evaluador si se trata de una expresión.
4. Utilice el contexto para la salida, la tabla de símbolos para los nombres
   y las clases de error del dominio para los diagnósticos.
5. Añada casos positivos, negativos y de límites en la suite correspondiente.
   Actualice los conteos esperados del verificador cuando cambie la cobertura.
6. Documente la instrucción en el catálogo y las reglas semánticas.

Para añadir una gráfica, amplíe `tipo_grafica` y los tokens, registre el tipo
en `src/graficas/tipos_grafica.py` e implemente su dibujo y selección en
`renderizar`. Reutilice el lienzo, las escalas y la fuente. Exponga los
cálculos estadísticos como funciones comprobables y añada pruebas del PNG y
de integración desde el DSL. Revise los valores predeterminados del Visitor.

## Verificación y entrega

```bash
python herramientas/verificar_entrega.py
python herramientas/crear_entrega.py --probar
```

La [guía de pruebas](../../ejercicios/pruebas/README.md) explica los modos y
los resultados contrastados. El [informe técnico](../13_cierre_tecnico.md)
conserva las evidencias registradas. Las [herramientas](../../herramientas/README.md)
permiten comprobar documentación, gramática e integridad del paquete.

## Límites de implementación

Las gráficas tienen tamaño fijo de 800 × 480 y salida PNG RGB de 8 bits,
sin transparencia, entrelazado ni antialiasing. El codificador utiliza filtro
0 y DEFLATE con Huffman fijo y LZ77. La fuente de 5 × 7 simplifica las tildes.
No se ofrecen escalas logarítmicas, ejes secundarios ni gráficas apiladas.

Los nombres de columna deben ser únicos. Los contratos de CSV y los límites
numéricos se explican en el [manual de usuario](usuario.md#conservación-de-datos-y-límites-numéricos).
La [guía de modelos](../11_guia_machine_learning.md) describe la separación de
entrenamiento y prueba: `evalua` utiliza la tabla recibida, sin crear una
partición automática.
