# AREPA — Manual de usuario

Este manual explica cómo instalar y usar AREPA para describir un análisis de
datos completo —cargar un CSV, limpiarlo, resumirlo y **graficarlo**— mediante
instrucciones del lenguaje. Incluye ejemplos de sintaxis y corrección de errores.

* Versión del intérprete: `AREPA v0.4 (Fase 3 - visualizacion y producto final)`.
* Para el mantenimiento y la ampliación del intérprete, consulte el [manual técnico](tecnico.md).

Índice:

1. [Qué es AREPA](#1-qué-es-arepa)
2. [Instalación](#2-instalación)
3. [Primeros pasos](#3-primeros-pasos)
4. [La sintaxis, por etapas](#4-la-sintaxis-por-etapas)
5. [Gráficas](#5-gráficas)
6. [Errores frecuentes](#6-errores-frecuentes)
7. [Caso de estudio paso a paso](#7-caso-de-estudio-paso-a-paso)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)
9. [Códigos de salida](#9-códigos-de-salida)

---

## 1. Qué es AREPA

AREPA (*Análisis Reproducible de datos Escrito con Palabras Autóctonas*) es un
lenguaje con vocabulario del español hablado en Colombia para escribir recetas
de datos. Un programa completo se ve así:

```text
quihubo
ventas = monte "datos/ventas.csv" con encabezado, separador ","

resumen = ventas
|> deje donde unidades > 0
|> cree total = unidades * precio
|> junte por [ciudad]
|> resuma ingreso = sume(total), registros = cuente()

cuenteme "Ciudades:", cuente(resumen)

pinte barras resumen
titulo "Ingresos por ciudad"
ejex ciudad
ejey ingreso
guardela "salidas/ingresos.png"

guarde resumen como "salidas/resumen_ciudades.csv"
chao
```

Todo programa empieza con `quihubo` y termina con `chao`, cada uno en su
propia línea. El salto de línea separa las instrucciones (no hay `;`).

---

## 2. Instalación

### 2.1 Requisitos

| Requisito | Para qué |
|---|---|
| **Python 3.11 o superior** (probado con 3.13) | Ejecutar el intérprete |
| **Git** | Descargar el repositorio |
| **Java 11 o superior** | **Solo** si vas a regenerar el lexer/parser; no hace falta para usar AREPA normalmente |

### 2.2 Pasos

```bash
# 1. Descargar el proyecto
git clone https://github.com/Pyromesis/Proyecto-Lenguajes-de-Programaci-n.git
cd Proyecto-Lenguajes-de-Programaci-n

# 2. Crear y activar un entorno virtual de Python
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar la única dependencia
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 4. Comprobar que quedó instalado
python3 src/cli/main.py --version
# AREPA v0.4 (Fase 3 - visualizacion y producto final)
```

Si `python3 --version` da menos de 3.11, actualízalo antes de continuar.

---

## 3. Primeros pasos

### 3.1 Tu primer programa

Crea un archivo `hola.arepa` con:

```text
quihubo
cuenteme "Hola, AREPA"
chao
```

### 3.2 Comprobar que está bien escrito

```bash
python3 src/cli/main.py hola.arepa
```

Salida:

```text
¡Quihubo pues! Programa bien escrito: 1 sentencia(s) reconocida(s).
```

### 3.3 Ejecutarlo

```bash
python3 src/cli/main.py hola.arepa --ejecutar
```

Salida (extracto):

```text
Hola, AREPA

¡De una! El programa corrió completo sin tropiezos.
```

### 3.4 Ver el árbol y los tokens (opcional)

```bash
python3 src/cli/main.py hola.arepa --arbol    # estructura del programa
python3 src/cli/main.py hola.arepa --tokens   # lista de tokens (piezas del texto)
```

### 3.5 Otros programas para practicar

Selección de programas de `ejemplos/`:

```bash
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar
```

---

## 4. La sintaxis, por etapas

### 4.1 Estructura obligatoria

```text
# comentario inicial opcional
quihubo
  <instrucciones>
chao
```

* `quihubo` y `chao` van cada uno en su línea.
* Los comentarios empiezan con `#` y llegan hasta el final de la línea; se
  pueden poner en cualquier parte.
* Cada instrucción termina en salto de línea.
* Se puede partir una instrucción larga después de `|>`, después de una coma o
  dentro de `( )` y `[ ]`.

### 4.2 Variables y expresiones

```text
precio = 15000
iva = precio * 0.19
total = precio + iva
es_caro = total > 20000
```

* Operadores: `+ - * / % ^` (potencia), comparaciones `== != < <= > >=`,
  lógicos `y`, `o`, `no`.
* Cadenas con comillas dobles: `"Bogotá"`, escapes `\n`, `\t`, `\\`, `\"`.
* Booleanos `obvio` / `falso`; valor faltante `nada`.
* `nada` se propaga: `nada + 1` da `nada`.
* `1/0` da `infinito`, `0/0` da `nada` (no detienen el programa).
* Los nombres de variables no pueden ser palabras reservadas (como `y`); los
  **nombres de columnas** sí.

### 4.3 Cargar y guardar

```text
ventas = monte "datos/ventas.csv" con encabezado, separador ","
guarde resumen como "salidas/resumen.csv"
```

* `con encabezado` indica que la primera fila trae los nombres de columna.
* `separador ";"` cambia el separador (por defecto se asume `,`).
* `guarde ... como ...` escribe la tabla en un CSV (crea la carpeta si falta).

### 4.4 El pipeline `|>` (preparar y resumir)

Cada línea del pipeline recibe la tabla de arriba y produce una nueva.

```text
limpias = ventas
|> escoja [fecha, ciudad, unidades, precio]      # elegir columnas
|> deje donde unidades > 0 y precio > 0          # filtrar filas
|> cree total = unidades * precio                # columna calculada
|> renombre ciudad -> municipio                  # renombrar
|> limpie duplicados                             # quitar repetidos
|> limpie vacios con 0                           # rellenar vacíos
|> acomode por [precio] pa_abajo                 # ordenar
|> convierta fecha -> fecha                      # convertir tipo
```

Tipos de conversión: `numero`, `texto`, `logico`, `fecha` (formato
`AAAA-MM-DD`).

Agrupar y resumir:

```text
resumen = limpias
|> junte por [ciudad]
|> resuma ingreso = sume(total), cuantos = cuente()
```

Agregaciones: `cuente()`, `sume(col)`, `promedie(col)`, `mediana(col)`,
`minimo(col)`, `maximo(col)`, `desviacion(col)`.

`describa tabla` imprime un resumen estadístico por columna numérica.

### 4.5 Estructuras en memoria (listas, registros, tablas)

```text
nums = [10, 20, 30]
persona = {nombre: "Ana", edad: 20}
gente = arme [nombre, edad] con [["Ana", 20], ["Luis", 31]]
```

* Los índices cuentan desde 1: `nums[1]` es `10`, `gente[1]["edad"]` es `20`.
* `agregue x en lista`, `saque 1 de lista`, `recorra fila en gente { ... }`.
* Fuera de `resuma`, las agregaciones usan `sume(gente, edad)`,
  `cuente(gente)`, `promedie(gente, edad)`, etc.
* Otras herramientas: `largo(x)`, `columna(tabla, nombre)`,
  `columnas(tabla)`.

### 4.6 Funciones, condicionales y ciclos

```text
invente doble(x) {
    devuelva x * 2
}

fijese_si (total > 100000) {
    cuenteme "Meta alcanzada"
} sino {
    cuenteme "Falta"
}

mientras (n > 1) {
    n = n - 1
}

repita 3 veces {
    cuenteme "vuelta"
}

repita i desde 1 hasta 10 paso 2 {
    cuenteme i
}
```

`pare` rompe el ciclo actual y `siga` salta a la siguiente vuelta.

---

## 5. Gráficas

Esta es la novedad de la Fase 3. La instrucción `pinte` dibuja una gráfica a
partir de una tabla y la exporta a PNG o la muestra.

### 5.1 Las cinco gráficas

| Tipo | Para qué sirve | Ejemplo |
|---|---|---|
| `barras` | comparar categorías | `pinte barras resumen` |
| `lineas` | evolución en el tiempo | `pinte lineas serie` |
| `histograma` | distribución de una columna | `pinte histograma ventas` |
| `dispersion` | relación entre dos números | `pinte dispersion ventas` |
| `cajas` | comparar niveles y dispersión por categoría | `pinte cajas ventas` |

### 5.2 Cómo se escribe

```text
pinte TIPO TABLA
titulo "Texto del título"
ejex columna_o_lista
ejey columna_o_lista
leyenda "Texto de la leyenda"
guardela "ruta/del/archivo.png"
```

* `titulo`, `ejex`, `ejey` y `leyenda` son opcionales y se pueden poner en
  cualquier orden; cada uno aparece **una sola vez**.
* `ejey` admite **varias series**: `ejey [col1, col2]` dibuja una serie por
  columna (con una leyenda distinta por color).
* El cierre es obligatorio para producir el archivo:
  * `guardela "ruta.png"`: guarda exactamente en esa ruta (debe terminar en
    `.png`).
  * `muestrela`: guarda la imagen en `salidas/<tabla>_<tipo>.png` y, si hay
    entorno gráfico, la abre en pantalla.
* Si no se pone cierre, la gráfica solo se valida y se prepara, no se guarda.

Ejemplo completo:

```text
pinte barras resumen
titulo "Ingresos por ciudad"
ejex ciudad
ejey ingreso
guardela "salidas/ingresos_ciudad.png"
```

### 5.3 Qué dibuja si no le dices las columnas

* **`ejex`**: usa la primera columna de texto o fecha; si no hay ninguna,
  numera las filas 1, 2, 3…
* **`ejey`**: usa todas las columnas numéricas.
* **`histograma`**: exige una sola columna en `ejey` e **ignora `ejex`**.
* **`dispersion` sin `ejex`**: usa la primera columna numérica como x.
* **`cajas`**: agrupa una caja por cada valor repetido de `ejex`; si cada valor
  es único, hace una caja por serie de `ejey`.

### 5.4 Ejecutar sin abrir ventanas

En servidores, contenedores o al correr el caso de estudio en lote, conviene no
abrir el visor:

```bash
python3 src/cli/main.py programa.arepa --ejecutar --sin-ventana
```

`--sin-ventana` (o la variable `AREPA_SIN_VENTANA=1`) hace que `muestrela`
guarde la imagen y **no** abra nada. Las imágenes siempre quedan en disco.

### 5.5 Tamaño y formato

Todas las gráficas son **PNG RGB de 800 × 480** y se generan con el motor
propio de AREPA (sin matplotlib). Dos ejecuciones del mismo programa producen
exactamente el mismo archivo.

---

## 6. Errores frecuentes

Un error real muestra su categoría, causa, archivo fuente, línea y columna,
la instrucción con un indicador `^` y una ayuda **Cómo corregir**. En una
conversión se identifica la fila; en CSV se distingue la línea del programa
de la línea del archivo de datos. Un error dentro de una función conserva
la ubicación de origen y hasta cinco llamadas para localizar su uso.

Las líneas empiezan en 1 y las columnas en 0. La ejecución se detiene al
primer error de ejecución; las instrucciones posteriores no se ejecutan.
El análisis léxico y sintáctico puede informar varios problemas antes de
que empiece la ejecución.

### 6.1 Resultados especiales y errores aritméticos

| Operación | Resultado de AREPA | Diagnóstico |
|---|---|---|
| `1 / 0` | `infinito` | Aviso: dividir por cero no está definido en los reales |
| `-1 / 0` | `-infinito` | El mismo aviso, conservando el signo del resultado |
| `0 / 0` | `nada` | Aviso: operación indeterminada |
| `5 % 0` | `nada` | Aviso: no existe un resto definido con divisor cero |
| `0 ^ -1` | `infinito` | Aviso: un exponente negativo implica dividir por cero |
| `(-1) ^ 0.5` | Sin resultado real admitido | Error: AREPA no representa números complejos |
| `nada + 1`, `nada / 0` | `nada` | Propagación normal de faltantes, sin aviso |

Los avisos se muestran por separado de `cuenteme`, incluyen la ubicación de
la operación y no cambian el resultado. Se agrupan las repeticiones de una
misma causa, ubicación y resultado para no inundar la consola; se muestran
hasta ocho grupos y se informa si quedan más. Las expresiones que no se
ejecutan no generan avisos. Validar sin `--ejecutar` tampoco ejecuta cálculos.

Para probar los diagnósticos y los casos que deben continuar sin error:

```bash
python ejercicios/pruebas/test_diagnosticos.py
python ejercicios/pruebas/ejecutar.py --completo
```

### 6.2 Errores frecuentes y corrección

| Problema | Corrección |
|---|---|
| Símbolo desconocido | Revise el carácter indicado en la fuente |
| Tipo de gráfica inválido | Use `barras`, `lineas`, `histograma`, `dispersion` o `cajas` |
| Variable o columna inexistente | Declare el nombre antes de usarlo y compruebe el encabezado |
| Archivo ausente | Revise la ruta desde el directorio donde ejecuta el programa |
| Salida gráfica con extensión incorrecta | Indique una ruta terminada en `.png` |
| Histograma con varias columnas | Seleccione una sola columna numérica mediante `ejey` |
| Cláusula gráfica repetida | Conserve una sola declaración de cada cláusula |
| Palabra reservada usada como variable | Elija otro identificador; `y`, por ejemplo, es un operador |

El [catálogo de instrucciones](../02_catalogo_instrucciones.md) contiene las
palabras reservadas y los ejemplos de sintaxis.

## 7. Caso de estudio paso a paso

El caso analiza AirPassengers, una serie de 144 observaciones mensuales
entre 1949 y 1960. Desde la raíz del proyecto:

```bash
python src/cli/main.py caso_estudio/programa.arepa --ejecutar --sin-ventana
```

Genera un resumen anual CSV y cinco gráficas en `caso_estudio/salidas/`.
El [caso de estudio](../../caso_estudio/README.md) explica las transformaciones,
los indicadores esperados y la interpretación de cada gráfica. La
[procedencia de los datos](../../caso_estudio/datos/FUENTE.md) documenta la
fuente y su integridad.

## 8. Preguntas frecuentes

**¿En qué idioma escribo los nombres?** Las variables y las
columnas admiten tildes y ñ. Las **palabras reservadas** van en minúscula y sin
tilde (`titulo`, `lineas`, `numero`).

**¿Cada cuánto separo instrucciones?** Una por línea. No hace falta `;`.

**¿Puedo partir una expresión en dos líneas?** Sí, después de `|>`, de una coma
o dentro de `( )`/`[ ]`.

**¿Por qué mi `muestrela` no abre ninguna ventana?** Porque no hay entorno
gráfico o porque definiste `--sin-ventana` / `AREPA_SIN_VENTANA=1`. La imagen
igual queda guardada.

**¿Dónde quedan las imágenes de `muestrela`?** En
`salidas/<nombre_tabla>_<tipo>.png`.

**¿Hay una consola interactiva?** Sí:

```bash
python3 src/cli/repl.py            # con autocompletado por Tab
python3 src/cli/repl.py --simple   # modo clásico
```

---

## 9. Códigos de salida

El programa de línea de comandos `src/cli/main.py` termina con:

| Código | Significado |
|---|---|
| `0` | El programa es válido (y, con `--ejecutar`, corrió sin errores) |
| `1` | El programa tiene errores léxicos, sintácticos o de ejecución |
| `2` | Problemas de argumentos o lectura del programa |

Opciones del CLI:

| Opción | Efecto |
|---|---|
| `--ayuda`, `--help`, `-h` | Muestra la ayuda y sale |
| `--version` | Muestra la versión |
| `--arbol` | Muestra el árbol de análisis |
| `--tokens` | Muestra la lista de tokens |
| `--ejecutar` | Ejecuta el programa con la biblioteca propia |
| `--sin-ventana` | No abre visores externos (equivale a `AREPA_SIN_VENTANA=1`) |

Cuando se ejecuta con `--ejecutar`, al final se imprime la lista
`Archivos generados:` con la ruta, el tipo y el tamaño de cada archivo.

## Conservación de datos y límites numéricos

En CSV, las comillas conservan un campo como texto exacto. Así, `" Ana "`,
`""`, `"001"` y `"obvio"` no pierden espacios ni cambian de tipo al releerse.
Para calcular con un número citado se usa `convierta columna -> numero`.
Sin comillas se infieren números y lógicos, y un campo vacío o `nada`
representa un faltante. `guarde` aplica estas reglas automáticamente.
Un encabezado o una tabla con nombres de columna repetidos se rechaza.

Se pueden calcular y mostrar enteros de más de 4.300 dígitos sin configurar
Python. Los modelos y métricas requieren números decimales finitos y tienen
el rango propio de esa representación. La regresión rechaza la divergencia
con una explicación para reducir la tasa o la escala; no informa métricas
NaN como si fueran un resultado exitoso. Pocas épocas de entrenamiento no
son un error si los resultados siguen siendo finitos.
