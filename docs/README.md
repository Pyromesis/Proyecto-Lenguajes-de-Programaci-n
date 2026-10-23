# Documentación de AREPA

Índice de la documentación del proyecto. Los documentos conservan su número
(`docs/01`, `docs/02`, …) porque el resto de informes los cita con esa
convención.

## Referencia del lenguaje

| Documento | Contenido |
|---|---|
| [`01_documento_alcance.md`](01_documento_alcance.md) | alcance, usuarios, entradas, salidas y restricciones |
| [`02_catalogo_instrucciones.md`](02_catalogo_instrucciones.md) | catálogo completo de instrucciones, palabras reservadas y ejemplos |
| [`03_gramatica_ebnf.md`](03_gramatica_ebnf.md) | gramática EBNF sincronizada con `gramatica/Arepa.g4` |
| [`05_arquitectura.md`](05_arquitectura.md) | arquitectura por capas y matriz funcionalidad → código → prueba |
| [`07_guia_sustentacion.md`](07_guia_sustentacion.md) | guion de la demostración y verificación paso a paso |
| [`09_reglas_semanticas.md`](09_reglas_semanticas.md) | reglas de tipos, errores y decisiones semánticas |

## Informes y matrices por corte

| Corte | Informe | Matriz de trazabilidad |
|---|---|---|
| 1 | [`04_informe_fase1.md`](04_informe_fase1.md) | [`06_matriz_trazabilidad_corte1.md`](06_matriz_trazabilidad_corte1.md) |
| 2 | [`08_informe_fase2.md`](08_informe_fase2.md) | [`10_matriz_trazabilidad_corte2.md`](10_matriz_trazabilidad_corte2.md) |
| 3 | [`11_informe_fase3.md`](11_informe_fase3.md) | [`12_matriz_trazabilidad_corte3.md`](12_matriz_trazabilidad_corte3.md) |

## Manuales

| Documento | Para quién |
|---|---|
| [`manuales/usuario.md`](manuales/usuario.md) | instalar, escribir programas y usar la CLI y las gráficas |
| [`manuales/tecnico.md`](manuales/tecnico.md) | arquitectura, gramática, runtime, motor PNG y cómo ampliar el lenguaje |

## Enunciado y evidencia

* [`Proyecto_LP.pdf`](Proyecto_LP.pdf): enunciado del curso.
* [`../caso_estudio/README.md`](../caso_estudio/README.md): caso de estudio
  reproducible con AirPassengers.
* [`../ejercicios/README.md`](../ejercicios/README.md): 164 ejercicios por corte.
* [`../salidas/README.md`](../salidas/README.md): evidencias CSV y PNG
  temporales.

## Verificación rápida

```bash
python3 herramientas/chequeo_gramatica.py      # 57/57 reglas, 65 reservadas
python3 herramientas/chequeo_pruebas.py        # 8 suites, 319 pruebas
python3 herramientas/chequeo_documentacion.py  # enlaces, referencias y conteos 32/120/12/6
bash herramientas/regresion_programas.sh       # 170 programas
bash herramientas/demo_sustentacion.sh         # demo completa
```
