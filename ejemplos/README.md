# Ejemplos oficiales AREPA (Linux)

Los 5 programas de referencia del lenguaje. Todos validan y ejecutan
desde la raíz del proyecto:

```bash
python3 src/cli/main.py ejemplos/demo.arepa
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
```

| Ejemplo | Qué demuestra | Exportación |
|---|---|---|
| `demo.arepa` | flujo completo: carga, pipeline, `junte`+`resuma`, `fijese_si`, `invente`, `pinte` y `guarde` | `salidas/resumen_ciudades.csv` |
| `filtros.arepa` | `monte` con `;`, `escoja`, `renombre`, `deje`, `cree`, `limpie`, `convierta`, `acomode`, `describa` | `salidas/filtros_listos.csv` |
| `graficas.arepa` | los 5 tipos (`barras`, `lineas`, `histograma`, `dispersion`, `cajas`) con `titulo`/`ejex`/`ejey`/`leyenda` | solo validación (PNG en Fase 3) |
| `funciones.arepa` | `invente`, `devuelva`, `sino` encadenado, `cuenteme`, `describa` | — |
| `ciclos.arepa` | `mientras`, `repita N veces`, `repita i desde/hasta/paso`, `pare`/`siga` + pipeline y `guarde` | `salidas/resumen_ciclos.csv` |

Los CSV generados están versionados como evidencia del Corte 2
(ver `salidas/README.md`). Más práctica (187 ejercicios) en
`Ejercicios_Problemas/README.md`.
