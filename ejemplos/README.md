# Ejemplos oficiales AREPA (Linux)

Los 6 programas de referencia del lenguaje. Todos validan y ejecutan
desde la raíz del proyecto:

```bash
python3 src/cli/main.py ejemplos/demo.arepa
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
```

| Ejemplo | Qué demuestra | Exportación |
|---|---|---|
| `demo.arepa` | flujo completo: carga, pipeline, `junte`+`resuma`, `fijese_si`, `invente`, `pinte` y `guarde` | `salidas/resumen_ciudades.csv` |
| `filtros.arepa` | `monte` con `;`, `escoja`, `renombre`, `deje`, `cree`, `limpie`, `convierta`, `acomode`, `describa` | `salidas/filtros_listos.csv` |
| `graficas.arepa` | los 5 tipos (`barras`, `lineas`, `histograma`, `dispersion`, `cajas`) con `titulo`/`ejex`/`ejey` y `guardela`/`muestrela` | 5 PNG en `salidas/` |
| `funciones.arepa` | `invente`, `devuelva`, `sino` encadenado, `cuenteme`, `describa` | — |
| `ciclos.arepa` | `mientras`, `repita N veces`, `repita i desde/hasta/paso`, `pare`/`siga` + pipeline y `guarde` | `salidas/resumen_ciclos.csv` |
| `memoria.arepa` | `arme` de tabla en memoria, acceso indexado 1-based, `recorra`, agregaciones fuera de `resuma`, `resuma` por categoría y `guarde` | `salidas/memoria_resumen.csv` |

`graficas.arepa` escribe sus 5 PNG en `salidas/`: con `guardela`
`barras.png`, `histograma.png`, `dispersion.png` y `cajas.png`, y con
`muestrela` la gráfica de `lineas` queda en `salidas/ventas_lineas.png`
(además intenta abrirla; sin entorno gráfico o con `--sin-ventana` solo
informa por consola). Los CSV de los ejemplos están versionados como
evidencia de los Cortes 2 y 3; los PNG son temporales e ignorados por
git (ver `salidas/README.md`). Más práctica (164 ejercicios por corte) en
`ejercicios/README.md`.
