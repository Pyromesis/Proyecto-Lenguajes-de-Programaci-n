# AREPA — Manual de usuario

Este manual explica cómo instalar y usar AREPA para describir un análisis de
datos completo —cargar un CSV, limpiarlo, resumirlo y **graficarlo**— sin
programar en Python. Está pensado para alguien que maneja hojas de cálculo y
algo de estadística, pero que no es programador.

* Versión del intérprete: `AREPA v0.4 (Fase 3 - visualizacion y producto final)`.
* Todo el motor (datos **y** gráficas) es propio: solo necesita Python y un
  paquete de ANTLR para ejecutar.
* Si buscas el detalle interno (arquitectura, algoritmos, cómo extender), mira
  `tecnico.md`.

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
| **Linux** con terminal | Entorno oficial del proyecto |
| **Python 3.11 o superior** (probado con 3.13) | Ejecutar el intérprete |
| **Git** | Descargar el repositorio |
| **Java 11 o superior** | **Solo** si vas a regenerar el lexer/parser; no hace falta para usar AREPA normalmente |

No hace falta instalar pandas, NumPy ni Matplotlib: el proyecto no las usa.

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

> **Nota sobre Java**: solo se necesita para regenerar el lexer y el parser a
> partir de `gramatica/Arepa.g4` (comando `./generar_gramatica.sh`). El código
> ya generado vive en `generado/`, así que para **usar** AREPA no hace falta
> Java.

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

Los `ejemplos/` traen seis programas listos:

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

AREPA explica los errores **en español, con línea y columna**, y señala el
lugar exacto con un caret `^`. Estos son mensajes reales del intérprete.

### 6.1 Un símbolo que no existe

```text
Encontré 2 problema(s), revisá esto:
  [léxico] Línea 2, Columna 6: Hay un símbolo '@' que no hace parte del lenguaje AREPA
```

**Qué hacer:** revisa la línea 2, columna 6 (empezando a contar en 1).

### 6.2 Un tipo de gráfica mal escrito

```text
  [sintáctico] Línea 3, Columna 6: Hace falta 'barras', 'lineas', 'histograma', 'dispersion', 'cajas' cerca de 'pastel'
  Línea 3: pinte pastel ventas
                 ^
```

**Qué hacer:** usa uno de los cinco tipos válidos.

### 6.3 Columna que no existe en la gráfica

```text
Error de gráfico durante la ejecución:
  Línea 4, Columna 0: La grafica usa la columna 'no_existe' que no existe en 'ventas'. Columnas: fecha, ciudad, categoria, unidades, precio.
  Línea 4: ejey no_existe
           ^
```

**Qué hacer:** revisa cómo se llaman tus columnas y escribe el nombre exacto.

### 6.4 Ruta sin `.png`

```text
Error de gráfico durante la ejecución:
  Línea 5, Columna 0: La ruta 'salidas/x.jpg' debe terminar en '.png' (extension esperada para guardar la grafica).
```

**Qué hacer:** cambia la ruta para que termine en `.png`.

### 6.5 Histograma con dos columnas

```text
Error de gráfico durante la ejecución:
  Línea 3, Columna 0: El histograma necesita exactamente una columna numerica en 'ejey' y la tabla 'ventas' tiene 2: unidades, precio. Indique una con 'ejey <columna>'.
```

**Qué hacer:** añade `ejey unidades` (o la columna que quieras).

### 6.6 Clausula repetida

```text
Error de gráfico durante la ejecución:
  Línea 5, Columna 0: La clausula 'titulo' esta repetida en la grafica; indiquela una sola vez.
```

**Qué hacer:** deja un solo `titulo` (vale para `ejey` y `leyenda` también).

### 6.7 Variable o columna inexistente

```text
Error de semántico durante la ejecución:
  Línea 2, Columna 4: El nombre 'y' no existe ni como columna ni como variable.
  Línea 2: x = y + 1
               ^
```

**Qué hacer:** declara la variable antes de usarla, o revisa el nombre de la
columna.

### 6.8 Archivo que no se encuentra

```text
Error de ejecución durante la ejecución:
  No encontré el archivo 'datos/no_existe.csv'. Revisá la ruta relativa al directorio desde donde corres el programa.
```

**Qué hacer:** las rutas son **relativas a la carpeta desde la que ejecutas**.
Corre siempre desde la raíz del proyecto o ajusta la ruta.

### 6.9 Usar una palabra reservada como variable

```text
  [sintáctico] Línea 2, Columna 0: No esperaba 'y' por ahí; revisá si sobra. En esa posición se esperaba 'chao', 'guarde', 'pinte', 'invente', 'devuelva', 'fijese_si', entre otras opciones. Ojo: el operador lógico 'y' (conjunción) es una palabra reservada, no puede usarse como nombre de variable; escogé otro nombre.
```

**Qué hacer:** cambia el nombre de la variable. La lista completa de palabras
reservadas está en `docs/02_catalogo_instrucciones.md`.

---

## 7. Caso de estudio paso a paso

El caso cierra el recorrido con datos reales: la serie mensual de pasajeros
internacionales (AirPassengers) entre 1949 y 1960, con 144 observaciones.

### 7.1 Ejecutarlo

Desde la raíz del proyecto:

```bash
AREPA_SIN_VENTANA=1 python3 src/cli/main.py caso_estudio/programa.arepa --ejecutar
```

Salida esperada (extracto):

```text
Registros limpios: 144
Total pasajeros: 40363
Promedio mensual: 280.2986111111111
Mediana mensual: 265.5
Minimo mensual: 104
Maximo mensual: 622
Total 1949: 1520
Total 1960: 5714
Crecimiento 1949-1960 (%): 275.92105263157896
[guarde] La tabla 'resumen' quedo escrita en 'caso_estudio/salidas/pasajeros_por_anio.csv' (12 filas).
[pinte] Grafica de lineas guardada en 'caso_estudio/salidas/01_serie.png' (13886 bytes, 800x480).
...
¡De una! El programa corrió completo sin tropiezos.
```

### 7.2 Qué produce

| Archivo | Qué contiene |
|---|---|
| `caso_estudio/salidas/pasajeros_por_anio.csv` | Resumen anual (12 filas: `anio,total,promedio,maximo_mes,registros`) |
| `caso_estudio/salidas/01_serie.png` | Serie mensual (líneas) |
| `caso_estudio/salidas/02_barras.png` | Total anual (barras) |
| `caso_estudio/salidas/03_histograma.png` | Distribución de los 144 meses |
| `caso_estudio/salidas/04_dispersion.png` | Periodo frente a pasajeros |
| `caso_estudio/salidas/05_cajas.png` | Cajas por década (1940s, 1950s, 1960s) |

### 7.3 Qué hace el programa, en palabras

1. Carga `caso_estudio/datos/pasajeros.csv`.
2. Filtra los meses con pasajeros y crea dos columnas: `periodo` (año + mes en
   un eje continuo) y `decada` (etiqueta legible `"1940s"`, `"1950s"`,
   `"1960s"`).
3. Agrupa por año y resume: total, promedio, máximo del mes y número de
   registros.
4. Imprime los indicadores clave (total, promedio, mediana, mínimo, máximo,
   totales de 1949 y 1960 y el crecimiento).
5. Guarda el resumen anual en CSV y dibuja las cinco gráficas.

El análisis completo, con su interpretación, está en
`caso_estudio/README.md`.

---

## 8. Preguntas frecuentes

**¿Necesito saber Python?** No. Solo copiar y pegar los comandos de
instalación y ejecución.

**¿Necesito pandas, NumPy o Matplotlib?** No. AREPA implementa todo (incluido
el motor de gráficas) por dentro. La única dependencia externa es el runtime de
ANTLR.

**¿En qué idioma escribo los nombres?** Como quieras: las variables y las
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

**¿Cómo sé cuántas pruebas tiene el proyecto?** Con
`python3 herramientas/chequeo_pruebas.py` (8 suites, 319 pruebas).

**¿La gramática y la documentación están sincronizadas?** Con
`python3 herramientas/chequeo_gramatica.py` (57 reglas, 65 reservadas).

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
| `2` | No se pudo leer el archivo (ruta inexistente) |

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
