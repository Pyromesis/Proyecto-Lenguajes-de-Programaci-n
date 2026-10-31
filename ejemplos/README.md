# Ejemplos oficiales AREPA (Linux)

Los 9 programas de referencia del lenguaje. Todos validan y ejecutan
desde la raíz del proyecto:

```bash
python3 src/cli/main.py ejemplos/demo.arepa
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
```

| Ejemplo | Qué demuestra | Exportación |
|---|---|---|
| `demo.arepa` | flujo completo: carga, pipeline, `junte`+`resuma`, `fijese_si`, `invente`, `pinte` y `guarde` | `salidas/resumen_ciudades.csv` |
| `memoria.arepa` | `arme` de tabla en memoria, acceso indexado 1-based, `recorra`, agregaciones fuera de `resuma`, `resuma` por categoría y `guarde` | `salidas/memoria_resumen.csv` |
| `filtros.arepa` | `monte` con `;`, `escoja`, `renombre`, `deje`, `cree`, `limpie`, `convierta`, `acomode`, `describa` | `salidas/filtros_listos.csv` |
| `graficas.arepa` | los 5 tipos (`barras`, `lineas`, `histograma`, `dispersion`, `cajas`) con `titulo`/`ejex`/`ejey` y `guardela`/`muestrela` | 5 PNG en `salidas/` |
| `funciones.arepa` | `invente`, `devuelva`, `sino` encadenado, `cuenteme`, `describa` | — |
| `ciclos.arepa` | `mientras`, `repita N veces`, `repita i desde/hasta/paso`, `pare`/`siga` + pipeline y `guarde` | `salidas/resumen_ciclos.csv` |
| `regresion.arepa` | `entrene ... regresion`, `prediga`, `evalua` y `guarde` | `salidas/regresion_casas.csv` |
| `clasificacion.arepa` | `entrene ... perceptron`, `clases`, `clasifique` y `evalua` | `salidas/clasificacion_estudiantes.csv` |
| `arbol_decision.arepa` | `entrene ... arbol`, `profundidad`, `min_hojas`, `clasifique` y `evalua` | `salidas/arbol_riesgo.csv` |

`graficas.arepa` escribe sus 5 PNG en `salidas/`: con `guardela`
`barras.png`, `histograma.png`, `dispersion.png` y `cajas.png`, y con
`muestrela` la gráfica de `lineas` queda en `salidas/ventas_lineas.png`
(además intenta abrirla; sin entorno gráfico o con `--sin-ventana` solo
informa por consola). Los 7 CSV de los ejemplos están versionados como
evidencia de datos, estructuras y machine learning; los PNG son temporales e
ignorados por git (ver `salidas/README.md`). Más práctica (164 ejercicios por
corte) en `ejercicios/README.md`.
