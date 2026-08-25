# AREPA — Documento de alcance (Fase 1)

**AREPA**: *Análisis Reproducible de datos Escrito con Palabras Autóctonas*
Lenguaje de dominio específico (DSL) para ciencia de datos y visualización.
Curso: Lenguajes de Programación y Transducción — Universidad Sergio Arboleda, 2026-2.

---

## 1. Delimitación del dominio

AREPA es un lenguaje declarativo que permite describir, en un solo programa,
las etapas principales de un flujo reproducible de análisis de datos:

1. **Carga y almacenamiento** — leer archivos CSV asociándolos a un identificador
   y guardar tablas resultantes.
2. **Selección y preparación** — escoger columnas, filtrar registros, ordenar,
   renombrar, crear columnas calculadas, limpiar duplicados y vacíos, convertir tipos.
3. **Transformación y análisis** — agrupar por una o varias variables y calcular
   agregaciones (conteo, suma, promedio, mediana, mínimo, máximo, desviación estándar).
4. **Visualización** — describir gráficas de barras, líneas, histogramas,
   dispersión y cajas con título, ejes y leyenda; mostrarlas o exportarlas a PNG.

**Fuera del dominio (no-objetivos):** AREPA no es un lenguaje de propósito general.
No busca reemplazar a Python ni ofrecer estructuras de datos arbitrarias,
concurrencia, programación orientada a objetos o acceso a redes.

## 2. Usuarios

| Perfil | Descripción | Qué hace con AREPA |
|---|---|---|
| Analista de datos | Conoce hojas de cálculo y algo de estadística; no programa en Python | Escribe programas cortos para cargar, limpiar, resumir y graficar datos |
| Estudiante / docente | Usa el lenguaje para aprender conceptos de lenguajes (léxico, sintaxis, semántica) | Estudia gramática, árboles de análisis y mensajes de error |
| Equipo desarrollador | Mantiene el intérprete | Extiende la gramática y las reglas semánticas |

## 3. Casos de uso

1. **Reporte de ventas por ciudad**: cargar CSV → filtrar registros válidos →
   columna calculada `total` → agrupar por ciudad → resumen de ingresos → gráfica de barras → exportar PNG y CSV.
2. **Depuración de una encuesta**: eliminar duplicados, rellenar vacíos,
   convertir tipos y ordenar.
3. **Comparación de indicadores**: funciones reutilizables (`invente`) para
   convertir unidades y condicionales (`fijese_si`) para validar umbrales.

## 4. Entradas

* Un **archivo fuente** con extensión `.arepa` escrito en UTF-8.
* (A partir de la Fase 2) los **archivos CSV** referenciados por `monte`.

## 5. Salidas

**Fase 1 (esta entrega):**
* Confirmación de que el programa pertenece al lenguaje.
* La lista de tokens (opcional, con `--tokens`).
* El **árbol de análisis** (opcional, con `--arbol`).
* Diagnósticos de error léxico y sintáctico con número de **línea y columna**.

**Fases 2 y 3:** tablas procesadas, CSV exportados, estadísticas y gráficas PNG.

## 6. Restricciones

1. Los programas inician con `quihubo` y terminan con `chao`.
2. Las palabras reservadas se escriben en minúscula y sin tildes.
3. Un salto de línea separa sentencias; se puede continuar una expresión en la
   línea siguiente después de `|>`, de una coma o dentro de paréntesis/corchetes.
4. Los comentarios inician con `#` y llegan al final de la línea.
5. Las variables del programa no pueden llamarse igual que una palabra reservada;
   los nombres de columnas sí pueden (provienen de archivos externos).
6. La Fase 1 reconoce programas pero **no los ejecuta**: no hay Visitor semántico,
   ni lectura real de CSV, ni generación de gráficas.

## 7. Alcance funcional de esta fase (Corte 1)

| Capacidad mínima exigida | Estado |
|---|---|
| Asignaciones y expresiones básicas (aritmética, relacional, lógica) | ✔ reconocidas |
| Carga de CSV (`monte`, con opciones de encabezado y separador) | ✔ reconocida |
| Selección de columnas (`escoja`) | ✔ reconocida |
| Filtros con comparaciones sencillas (`deje donde`) | ✔ reconocidos |
| Reconocimiento sintáctico de visualización (`pinte ... guardela/muestrela`) | ✔ reconocido (aún no produce gráficas) |
| Gramática BNF/EBNF documentada | ✔ `docs/03_gramatica_ebnf.md` |
| Gramática implementada en ANTLR4 (lexer + parser Python) | ✔ `gramatica/Arepa.g4`, `generado/` |
| Pruebas léxicas y sintácticas positivas y negativas | ✔ 16/16 (`pruebas/`) |
| Reporte de errores comprensibles con línea y columna | ✔ `src/errores.py` |
| Interfaz de línea de comandos | ✔ `src/main.py` |

## 8. Criterios de éxito

* El sistema **reconoce programas correctos** del DSL, genera el árbol de análisis
  y reporta errores comprensibles en programas incorrectos.
* Toda decisión de diseño está justificada en el catálogo de instrucciones.
* El proyecto es reproducible: dependencias declaradas y pasos documentados.
