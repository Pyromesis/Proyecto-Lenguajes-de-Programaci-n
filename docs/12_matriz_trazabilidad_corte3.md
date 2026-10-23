# AREPA — Matriz de trazabilidad del Corte 3 (Linux)

Correspondencia verificable entre cada requisito del Corte 3 del enunciado
(`docs/Proyecto_LP.pdf`, sección 5) y su evidencia en el repositorio.

Convenciones: "ANTLR" remite a `gramatica/Arepa.g4` con su línea; "Prueba"
remite a `pruebas/` (todos los nombres completos son
`pruebas/<archivo>::<caso>`); "Evidencia" remite a la ruta real del archivo
generado o del documento.

Reglas aplicadas: `docs/09_reglas_semanticas.md` (§8 y §9).
Motor gráfico: `docs/11_informe_fase3.md` (§3).
Caso de estudio: `caso_estudio/README.md`.

Verificación previa del entorno:

```bash
python3 herramientas/chequeo_gramatica.py         # 57/57 reglas, 65 reservadas
.venv/bin/python herramientas/chequeo_pruebas.py  # 8 suites, 319 pruebas
.venv/bin/python pruebas/test_proyecto.py         # 8 de 8 suites
AREPA_SIN_VENTANA=1 .venv/bin/python src/cli/main.py caso_estudio/programa.arepa --ejecutar
bash herramientas/demo_sustentacion.sh
```

---

## 1. Requisitos del Corte 3

| ID | Requisito del enunciado | Documento | Gramática (`.g4`) | Código | Prueba | Evidencia | Estado |
|----|-------------------------|-----------|-------------------|--------|--------|-----------|--------|
| T01 | Al menos cuatro tipos de gráficas | `docs/11` §2 y §3.5 | `tipo_grafica` (229), `BARRAS`…`CAJAS` (443-447) | `src/graficas/tipos_grafica.py` (`TIPOS`, 54; `_dibujar_*`) | `test_graficas.py::runtime_los_cinco_tipos_generan_png_valido` | `salidas/*.png` (5 tipos) | VERIFICADO |
| T02 | Barras | `docs/11` §3.5 | `BARRAS` (443) | `tipos_grafica.py::_dibujar_barras` (679) | `test_graficas.py::barras_genera_png_valido`, `::barras_suma_categorias_repetidas` | `salidas/barras.png` | VERIFICADO |
| T03 | Líneas | `docs/11` §3.5 | `LINEAS` (444) | `tipos_grafica.py::_dibujar_lineas` (752) | `test_graficas.py::lineas_genera_png_valido_con_dos_series`, `::runtime_ejey_con_lista_genera_dos_series` | `salidas/ventas_lineas.png` | VERIFICADO |
| T04 | Histograma | `docs/11` §3.5 y §5.1 | `HISTOGRAMA` (445) | `tipos_grafica.py::_dibujar_histograma` (794), `cubetas_histograma` (355) | `test_graficas.py::histograma_genera_png_valido`, `::histograma_usa_las_cubetas_esperadas`, `::runtime_histograma_con_dos_columnas_falla` | `salidas/histograma.png` | VERIFICADO |
| T05 | Dispersión | `docs/11` §3.5 y §5.1 | `DISPERSION` (446) | `tipos_grafica.py::_dibujar_dispersion` (862) | `test_graficas.py::dispersion_genera_png_valido` | `salidas/dispersion.png` | VERIFICADO |
| T06 | Cajas | `docs/11` §3.5 y §6 | `CAJAS` (447) | `tipos_grafica.py::_dibujar_cajas` (898), `cuartiles` (326) | `test_graficas.py::cajas_genera_png_valido`, `::cajas_cuartiles_con_datos_conocidos` | `salidas/cajas.png`, `caso_estudio/salidas/05_cajas.png` | VERIFICADO |
| T07 | Configuración desde el DSL: título | `docs/02` §3.4 | `clausula_estetica` (237), `TITULO` (448) | `src/runtime/ejecutor.py::visitInstruccion_grafica` (502) | `test_graficas.py::runtime_titulo_y_leyenda_en_cualquier_orden_cambian_el_png` | `caso_estudio/programa.arepa:72` (`titulo`) | VERIFICADO |
| T08 | Configuración desde el DSL: ejes | `docs/02` §3.4 | `EJEX` (449), `EJEY` (450); `clausula_estetica:239-240` | `ejecutor.py::_columnas_de_clausula` (749), `_validar_eje_x` (825) | `test_graficas.py::runtime_columna_inexistente_en_ejey_falla`, `::eje_x_espacia_etiquetas_largas_sin_recortarlas` | `caso_estudio/programa.arepa:73-74` | VERIFICADO |
| T09 | Varias series en `ejey [col1, col2]` | `docs/02` §3.4 | `clausula_estetica:240` `EJEY NL* (nombre_columna \| lista_literal)` | `ejecutor.py::_columnas_de_clausula` (749); `tipos_grafica.py::Grafica` (400) | `test_graficas.py::runtime_ejey_con_lista_genera_dos_series` | `gramatica/Arepa.g4:240` | VERIFICADO |
| T10 | Leyenda | `docs/02` §3.4 | `LEYENDA` (451) | `tipos_grafica.py::_leyenda` (532) | `test_graficas.py::runtime_titulo_y_leyenda_en_cualquier_orden_cambian_el_png` | — (cubierto por prueba) | VERIFICADO |
| T11 | Exportación a PNG (`guardela`) | `docs/02` §3.4 | `final_grafica` (244), `GUARDELA` (452) | `src/graficas/png.py::codificar_png` (523), `escribir_png` (561); `ejecutor.py::_guardar_png` (847) | `test_graficas.py::runtime_barras_guardela_escribe_png_y_registra_archivo` | `caso_estudio/salidas/01_serie.png` … `05_cajas.png` | VERIFICADO |
| T12 | PNG válido RGB 800x480 | `docs/11` §3.1 | — | `png.py` (`IHDR`, 523) | `test_graficas.py::firma_ihdr_idat_iend_en_orden`, `::roundtrip_fijo_conserva_las_scanlines`, `::tamano_descomprimido_es_exacto` | `file caso_estudio/salidas/*.png` → `PNG image data, 800 x 480, 8-bit/color RGB` | VERIFICADO |
| T13 | CRC-32 y Adler-32 propios | `docs/11` §3.1 | — | `png.py::crc32` (78), `::adler32` (94) | `test_graficas.py::crc32_vector_conocido_y_comparacion_independiente`, `::adler32_vector_conocido`, `::chunks_llevan_crc_valido` | — | VERIFICADO |
| T14 | DEFLATE fijo + LZ77 propio | `docs/11` §3.1 | — | `png.py::_comprimir_fijo` (392), `::_BuscadorLz77` (322) | `test_graficas.py::roundtrip_fijo_conserva_las_scanlines`, `::color_solido_comprime_de_forma_clara`, `::roundtrip_guardado_con_mas_de_un_bloque` | — | VERIFICADO |
| T15 | `muestrela` (mostrar o guardar en `salidas/`) | `docs/02` §3.4 | `MUESTRELA` (453) | `ejecutor.py` (muestrela → `salidas/<tabla>_<tipo>.png`), `_abrir_grafica` (863) | `test_graficas.py::runtime_muestrela_escribe_en_salidas_sin_ventana` | `salidas/ventas_lineas.png` | VERIFICADO |
| T16 | Ejecución por consola (`--ejecutar`) | `docs/01` §5 | — | `src/cli/main.py::main` (121), `::_ejecutar` (231) | `test_graficas.py::runtime_barras_guardela_escribe_png_y_registra_archivo` | salida de `--ejecutar` con `[pinte] …` | VERIFICADO |
| T17 | `--sin-ventana` (CI / sin entorno gráfico) | `docs/02` | — | `main.py` (`--sin-ventana`, 167); `ejecutor.py` (`AREPA_SIN_VENTANA`, 865) | `test_graficas.py::runtime_muestrela_escribe_en_salidas_sin_ventana` | `AREPA_SIN_VENTANA=1 … --ejecutar` | VERIFICADO |
| T18 | `--ayuda` / `--version` del CLI | `docs/manuales/usuario.md` §7 | — | `main.py` (141-154) | `bash herramientas/demo_sustentacion.sh` paso 5b | `python3 src/cli/main.py --version` | VERIFICADO |
| T19 | Errores con línea, columna y caret | `docs/01` §5 | — | `main.py::_mostrar_contexto` (74); `src/errores_base.py::ErrorGrafica` (83) | `test_graficas.py::runtime_columna_inexistente_en_ejey_falla`, `::runtime_ruta_sin_png_falla` | salida real del CLI | VERIFICADO |
| T20 | Caso de estudio con datos públicos | `caso_estudio/README.md` | — | `caso_estudio/programa.arepa` | `test_graficas.py::caso_estudio_ejecuta_desde_la_raiz_sin_errores` | `caso_estudio/datos/pasajeros.csv` (144 filas), `datos/FUENTE.md` | VERIFICADO |
| T21 | Cinco PNG + CSV del caso de estudio | `caso_estudio/README.md` §8 | — | `caso_estudio/programa.arepa:67-102` | `test_graficas.py::caso_estudio_genera_cinco_png_y_el_csv_anual` | `caso_estudio/salidas/` (6 archivos) | VERIFICADO |
| T22 | Indicadores del caso verificables | `caso_estudio/README.md` §5 | — | `caso_estudio/programa.arepa:56-64` | `test_graficas.py::caso_estudio_imprime_los_indicadores_clave` | `Total pasajeros: 40363` | VERIFICADO |
| T23 | Determinismo del caso de estudio | `caso_estudio/README.md` §8 | — | `png.py` (LZ77 voraz + Huffman fijo) | `test_graficas.py::caso_estudio_es_idempotente_y_determinista` | `sha256sum caso_estudio/salidas/*` | VERIFICADO |
| T24 | Pruebas de regresión (programas completos) | `docs/11` §8 | — | `ejemplos/`, `ejercicios/` | 170 programas con `--ejecutar` sin fallos | `herramientas/regresion_programas.sh` | VERIFICADO |
| T25 | Suite de pruebas unificada | `pruebas/README.md` | — | `pruebas/test_proyecto.py`, `test_graficas.py` | 8 suites, 319 pruebas | `.venv/bin/python herramientas/chequeo_pruebas.py` | VERIFICADO |
| T26 | Manual de usuario | `docs/manuales/usuario.md` | — | — | comandos y ejemplos del manual | `docs/manuales/usuario.md` | VERIFICADO |
| T27 | Manual técnico | `docs/manuales/tecnico.md` | — | — | referencias archivo:línea del manual | `docs/manuales/tecnico.md` | VERIFICADO |
| T28 | Documentación del corte (informe) | `docs/11_informe_fase3.md` | — | — | este informe | `docs/11_informe_fase3.md` | VERIFICADO |
| T29 | Matriz de trazabilidad del corte | este documento | — | — | — | `docs/12_matriz_trazabilidad_corte3.md` | VERIFICADO |
| T30 | Demo de sustentación reproducible | `docs/07_guia_sustentacion.md` §14 | — | `herramientas/demo_sustentacion.sh` | termina con `De una: demo de sustentación completa sin tropiezos.` | salida del script | VERIFICADO |
| T31 | Gramática sincronizada tras el Corte 3 | `docs/03_gramatica_ebnf.md` §6 | `clausula_estetica` (237) | `gramatica/Arepa.g4` | `python3 herramientas/chequeo_gramatica.py` → 57/57 y 65 | `docs/03` §6 | VERIFICADO |

---

## 2. Alcance mínimo del Corte 3 (resumen)

| Alcance exigido | Evidencia | Resultado |
|---|---|---|
| Cuatro o más tipos de gráfica | `barras`, `lineas`, `histograma`, `dispersion`, `cajas` (`tipos_grafica.py:54`) | OK (5) |
| Configuración desde el DSL (título, ejes, leyenda) | `titulo`, `ejex`, `ejey`, `leyenda` en `clausula_estetica:237-242` | OK |
| Exportación PNG | `guardela` escribe PNG RGB 800x480 (`png.py`, `ejecutor.py:847`) | OK |
| Ejecución por consola | `--ejecutar`, `--sin-ventana`, `--ayuda`, `--version` | OK |
| Caso de estudio con datos públicos | `caso_estudio/` (AirPassengers, 144 filas) con 5 PNG + CSV | OK |
| Pruebas de regresión | 170 programas con `--ejecutar` (incluye 12 ejercicios de gráficas); suite de gráficas de 63 casos | OK |
| Manuales | `docs/manuales/usuario.md`, `docs/manuales/tecnico.md` | OK |
| Documentación y demo | `docs/11`, `docs/12`, `herramientas/demo_sustentacion.sh` | OK |

---

## 3. Notas de decisiones intencionales (no son contradicciones)

* **Un tipo de gráfica con valor por defecto propio.** El histograma ignora
  `ejex` a propósito (las cubetas salen de la única columna de `ejey`) y exige
  exactamente esa columna; si no se indica, solo funciona cuando la tabla tiene
  una sola columna numérica. Cubierto por
  `test_graficas.py::runtime_histograma_con_dos_columnas_falla` (T04).
* **Las cajas agrupan por x repetida.** Es lo que pide el enunciado ("una caja
  por categoría"); el caso de estudio usa etiquetas `"1940s"`/`"1950s"`/
  `"1960s"` para tener tres cajas reales. Ver `docs/11` §6 y T06.
* **Sin antialiasing y tildes simplificadas** (F3 y F4 de `docs/11` §4): son
  decisiones documentadas, no defectos; los PNG son deterministas por diseño.
* **`muestrela` sin entorno gráfico** no falla: escribe igual el archivo y sólo
  avisa (`ejecutor.py:863`), lo que permite correr el caso de estudio en CI.

---

## 4. Reproducción paso a paso

```bash
cd Proyecto-Lenguajes-de-Programaci-n
source .venv/bin/activate

python3 herramientas/chequeo_gramatica.py          # 57/57 reglas, 65 reservadas
python3 herramientas/chequeo_pruebas.py            # 8 suites, 319 pruebas
python3 pruebas/test_proyecto.py                   # 8 de 8 suites

python3 src/cli/main.py ejemplos/graficas.arepa --ejecutar --sin-ventana
ls -l salidas/*.png

python3 src/cli/main.py caso_estudio/programa.arepa --ejecutar --sin-ventana
ls -l caso_estudio/salidas/

bash herramientas/demo_sustentacion.sh
```
