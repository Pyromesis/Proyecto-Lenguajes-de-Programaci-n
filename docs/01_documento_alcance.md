# AREPA — Documento de alcance (Fase 1)

**AREPA**: *Análisis Reproducible de datos Escrito con Palabras Autóctonas*
Lenguaje de dominio específico (DSL) para ciencia de datos y visualización.
Curso: Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2.

---

## 1. Delimitación del dominio

AREPA es un lenguaje declarativo con el que se puede escribir, en un solo
programa, el recorrido completo de un análisis de datos reproducible:

1. **Carga y almacenamiento**: leer archivos CSV y asociarlos a un nombre,
   además de guardar las tablas que se generen.
2. **Selección y preparación**: elegir columnas, filtrar filas, ordenar,
   renombrar, calcular columnas nuevas, eliminar duplicados y vacíos y
   convertir tipos.
3. **Transformación y análisis**: agrupar por una o varias variables y sacar
   agregaciones (conteo, suma, promedio, mediana, mínimo, máximo, desviación).
4. **Visualización**: describir gráficas de barras, líneas, histogramas,
   dispersión y cajas con su título, ejes y leyenda, para mostrarlas en
   pantalla o exportarlas a PNG.

Queda por fuera del dominio todo lo que no tenga que ver con ese flujo.
AREPA no pretende ser un lenguaje de propósito general: no busca reemplazar a
Python ni ofrecer estructuras de datos arbitrarias, concurrencia, programación
orientada a objetos o acceso a redes.

## 2. Usuarios

| Perfil | Descripción | Qué hace con AREPA |
|---|---|---|
| Analista de datos | Maneja hojas de cálculo y algo de estadística, pero no programa en Python | Escribe programas cortos para cargar, limpiar, resumir y graficar datos |
| Estudiante / docente | Usa el lenguaje para estudiar conceptos de lenguajes (léxico, sintaxis, semántica) | Revisa la gramática, los árboles de análisis y los mensajes de error |
| Equipo desarrollador | Mantiene el intérprete | Amplía la gramática y las reglas semánticas |

## 3. Casos de uso

1. **Reporte de ventas por ciudad**: se carga el CSV, se filtran los registros
   válidos, se calcula la columna `total`, se agrupa por ciudad y se resume el
   ingreso; al final se genera una gráfica de barras y se exporta a PNG y CSV.
2. **Depuración de una encuesta**: quitar duplicados, rellenar vacíos,
   convertir tipos y ordenar.
3. **Comparación de indicadores**: funciones reutilizables (`invente`) para
   convertir unidades y condicionales (`fijese_si`) para validar umbrales.

## 4. Entradas

* Un **archivo fuente** con extensión `.arepa` escrito en UTF-8.
* (Desde la Fase 2) los **archivos CSV** que mencione `monte`.

## 5. Salidas

**Fase 1 (esta entrega):**
* La confirmación de que el programa pertenece o no al lenguaje.
* La lista de tokens, si se pide con `--tokens`.
* El **árbol de análisis**, si se pide con `--arbol`.
* Diagnósticos de error léxico y sintáctico que dicen **línea y columna**.

**Fases 2 y 3:** tablas procesadas, CSV exportados, estadísticas y gráficas PNG.

## 6. Restricciones

1. Todo programa arranca con `quihubo` y termina con `chao`; cada uno va en
   su propia línea.
2. Las palabras reservadas van en minúscula y sin tildes.
3. El salto de línea separa sentencias; se puede continuar una expresión en la
   línea siguiente después de `|>`, de una coma o dentro de paréntesis/corchetes.
4. Los comentarios empiezan con `#` y corren hasta el final de la línea; se
   permiten en cualquier posición del programa.
5. Las variables del programa no pueden llamarse igual que una palabra
   reservada; los nombres de columnas sí pueden (vienen de archivos externos).
6. La Fase 1 reconoce programas pero **no los ejecuta**: no hay Visitor
   semántico, ni lectura real de CSV, ni generación de gráficas.

## 7. Alcance funcional de esta fase (Corte 1)

| Capacidad mínima exigida | Estado |
|---|---|
| Asignaciones y expresiones básicas (aritmética, relacional, lógica) | reconocidas |
| Carga de CSV (`monte`, con opciones de encabezado y separador) | reconocida |
| Selección de columnas (`escoja`) | reconocida |
| Filtros con comparaciones sencillas (`deje donde`) | reconocidos |
| Reconocimiento sintáctico de visualización (`pinte ... guardela/muestrela`) | reconocido (todavía no produce gráficas) |
| Gramática BNF/EBNF documentada | lista, en `docs/03_gramatica_ebnf.md` |
| Gramática implementada en ANTLR4 (lexer + parser Python) | lista, en `gramatica/Arepa.g4` y `generado/` |
| Pruebas léxicas y sintácticas positivas y negativas | 28 de 28 pasan (`pruebas/`, incluye 7 verificaciones de la CLI) |
| Reporte de errores comprensibles con línea y columna | listo, en `src/errores.py` |
| Interfaz de línea de comandos | lista, en `src/main.py` |

## 8. Criterios de éxito

* El sistema **reconoce programas correctos** del DSL, arma el árbol de
  análisis y reporta errores que se entienden cuando el programa está mal.
* Cada decisión de diseño queda justificada en el catálogo de instrucciones.
* El proyecto se puede reproducir: las dependencias están declaradas y los
  pasos quedaron documentados.
