# AREPA — Reglas semánticas (Corte 2, Linux)

Documento dedicado del entregable "documentación de reglas semánticas".
Todo se verifica en Linux con:

```bash
python3 pruebas/test_proyecto.py
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
python3 src/cli/main.py ejemplos/ciclos.arepa --ejecutar
python3 src/cli/main.py ejemplos/filtros.arepa --ejecutar
```

Referencia de implementación: `docs/05_arquitectura.md` (§4–§6),
`docs/02_catalogo_instrucciones.md` (§3.6, §4–§5),
`docs/08_informe_fase2.md`.

---

## 1. Modelo de valores

| Valor | Representación | Notas |
|---|---|---|
| número entero | `42` | aritmética binaria de Python |
| número decimal | `3.14` | `float`; `4.0` se exporta como `4` |
| texto | `"Bogotá"` | UTF-8; escapes `\\n \\t \\\\ \\" \\b \\r` |
| lógico | `obvio` / `falso` | únicos valores de condición |
| faltante | `nada` | estilo SQL: se propaga, nunca equivale |
| infinito | `infinito` / `-infinito` | solo como resultado de `1/0`, `-1/0`, desborde de `^` |

Conversión CSV → valor (`datos/tipos.py::texto_a_valor`): entero →
decimal → lógico (`obvio`/`falso`) → texto. Campo vacío → `nada`.

## 2. Expresiones y tipos (`expresiones/operadores.py`)

* `nada` se propaga: `nada + 1`, `nada == 5`, `obvio y nada` → `nada`.
* Comparaciones solo dentro del mismo género (número-número,
  texto-texto, lógico-lógico). Mezclar número con texto →
  `ErrorTipos`. Sin coerción número↔texto, sin concatenación con `+`.
* Lógicos exigen `obvio`/`falso`; `1 y obvio` → `ErrorTipos`.
* `1/0` → `infinito`, `-1/0` → `-infinito`, `0/0` → `nada`,
  `5%0` → `nada` (no tumban el runtime).
* `^` asociativa a derecha; `(-1) ^ 0.5` → `ErrorOperacion`
  (resultado complejo). Desborde → `infinito` con signo.
* Precedencia: `o` < `y` < `no` < comparación < `+ -` < `* / %` <
  `-` unario < `^`. El paréntesis altera el orden.

## 3. Nombres: variables vs columnas (`expresiones/evaluador.py`)

* Variable del programa: exige `ID` puro. Usar reservada (`y = 5`) →
  error sintáctico con pista.
* Columna de datos: acepta `ID` o cualquier reservada
  (`nombre_columna`, decisión D5) porque los encabezados vienen de
  CSV externos (`fecha`, `total`, …).
* Resolución `_resolver_nombre`: 1) columna de la fila en contexto,
  2) variable en `TablaSimbolos`, 3) `ErrorVariable` con columnas
  disponibles como pista. En modo agregación el nombre se pasa sin
  evaluar (`sume(precio)` recibe nombre, no valor).

## 4. Tabla de símbolos y ámbitos (`runtime/simbolos.py`)

* Ámbitos encadenados hijo→padre. `declarar` escribe en el actual;
  `buscar`/`asignar` suben por la cadena.
* `x = valor` declara si no existe en ningún ámbito visible y asigna
  si existe (semántica tipo Python).
* Solo las funciones `invente` crean ámbito (closure con el ámbito de
  definición, permite recursión). `fijese_si` y los ciclos NO crean
  ámbito: la variable del rango `repita i desde…` queda visible al
  terminar.
* Identificadores: letra Unicode (ñ, tildes) o `_` al inicio.

## 5. Pipeline de datos (`runtime/ejecutor.py`, `datos/tabla.py`)

* Cada etapa `|>` recibe una tabla y devuelve una NUEVA (D3: la
  entrada nunca se muta).
* Primera etapa: `monte` o valor evaluado. Toda etapa siguiente debe
  ser operación de datos; operar sin tabla de entrada →
  `ErrorOperacion`.
* `escoja [cols]`: toda columna debe existir, si no `ErrorColumna`.
* `deje donde COND`: conserva la fila solo si `COND` es exactamente
  `obvio`. `nada` o no-lógico descarta la fila (filtro) — pero en
  `fijese_si`/`mientras` el no-lógico es error (ver §7).
* `cree col = EXPR`: la columna no debe existir ya; evalúa por fila.
* `renombre A -> B`: `A` debe existir, `B` no debe existir.
* `acomode [cols]`: merge sort propio estable; `nada` siempre al
  final; dos `nada` son iguales (orden determinista).
* `limpie duplicados`: conserva primera aparición (clave = tupla);
  no admite `con VALOR` (→ `ErrorSemantico`).
  `limpie vacios con V`: rellena `nada` con `V`;
  `limpie vacios` solo: elimina filas con algún `nada`.
* `convierta COL -> tipo`: `numero`/`texto`/`logico`/`fecha`
  (fecha válida `AAAA-MM-DD` con bisiesto; si no, `ErrorTipos`).
* `junte por [cols]` + `resuma a = AGREG(...)`: agrupa conservando
  orden de primera aparición. El `junte` solo prepara el `resuma`
  inmediato: si otra operación se interpone, las claves rezagadas se
  descartan. Agregaciones:
  `cuente/sume/promedie/mediana/minimo/maximo/desviacion`
  (desviación poblacional). Los `nada` se ignoran; grupo vacío →
  `nada`. Llamar agregación fuera de `resuma` → `ErrorOperacion`;
  sobre columna inexistente → `ErrorColumna`.
* `describa TABLA`: resumen estadístico por columna numérica con las
  6 agregaciones; exige tabla.
* `monte RUTA`: lector propio UTF-8 (tolera BOM `utf-8-sig`), máquina
  de estados con comillas y `""`; fila con más campos que el
  encabezado o comillas sin cerrar → `ErrorCSV` con línea del
  archivo; con menos campos se rellena con `nada`. Archivo ausente o
  no UTF-8 → `ErrorArchivo`.
* `guarde TABLA como RUTA`: exige tabla; escritor propio UTF-8 sin
  BOM; crea la carpeta destino; entrecomilla si hay separador,
  comilla o salto. `guarde` sobre no-tabla → `ErrorOperacion`.

## 6. Funciones (`invente` / `devuelva` / llamada)

* `invente f(params) {…}` registra `FuncionArepa` (cuerpo + closure).
* La llamada crea ámbito hijo, enlaza argumentos (número exacto, si
  no `ErrorEjecucion`), ejecuta el cuerpo.
* `devuelva EXPR?` interrumpe con señal interna `RetornoFuncion`;
  fuera de función → error semántico.
* Recursión sin caso base → `ErrorEjecucion` en español (no
  `RecursionError` crudo).

## 7. Control: condicional y ciclos

* `fijese_si (COND) {…} sino {…}`: `COND` debe ser `obvio`/`falso`;
  `nada` u otro tipo → `ErrorTipos`.
* `mientras (COND) {…}`: reevalúa por vuelta; misma regla lógica.
* `repita N veces {…}`: `N` se evalúa una vez, exige entero ≥ 0;
  `0` no ejecuta el cuerpo.
* `repita i desde A hasta B (paso P) {…}`: extremos inclusivos; paso
  por defecto `1` (o `-1` si `A > B`); paso `0` → error; el bloque
  no crea ámbito.
* `pare` sale del ciclo más cercano; `siga` salta a la siguiente
  vuelta (señales internas `SalirCiclo`/`SeguirCiclo`). Fuera de
  ciclo → error semántico.
* Tope de seguridad: > 1 000 000 de vueltas → `ErrorEjecucion` que
  pide revisar condición/rango/paso (no se cuelga).

## 8. Visualización (`pinte`, solo validación en Corte 2)

* `pinte TIPO TABLA [cláusulas] [cierre]`: valida que la tabla exista
  y que `ejex`/`ejey` existan (`ErrorColumna` si no). No genera PNG;
  avisa que la imagen llega en Fase 3. Tipo inválido (`pastel`) →
  error sintáctico.

## 9. Catálogo de errores

| Clase | Cuándo |
|---|---|
| `ErrorVariable` | variable inexistente (con pista de columnas) |
| `ErrorColumna` | columna inexistente en `escoja/acomode/resuma/pinte/ejes` |
| `ErrorTipos` | mezcla número-texto, lógico con número, condición no lógica, conversión imposible |
| `ErrorOperacion` | operación sin tabla, agregación fuera de `resuma`, `guarde` sobre no-tabla, potencia compleja |
| `ErrorSemantico` / `ErrorEjecucion` | `devuelva`/`pare`/`siga` fuera de lugar, argumentos incorrectos, tope de ciclos, recursión profunda |
| `ErrorArchivo` / `ErrorCSV` | ruta ausente, no UTF-8, fila con exceso de campos, comillas sin cerrar |

Pruebas que los cubren: `test_expresiones.py` (tipos),
`test_runtime.py` (`variable_inexistente_rechazada`,
`escoja_columna_inexistente`, `suma_numero_mas_texto_rechazada`,
`operacion_sin_tabla_de_entrada_rechazada`,
`agregacion_fuera_de_resuma_rechazada`,
`guarde_sobre_variable_no_tabla_rechazado`,
`pare/siga fuera de ciclo`, `devuelva_fuera_de_funcion_rechazado`).
