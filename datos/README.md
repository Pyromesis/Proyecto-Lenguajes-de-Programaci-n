# Datos de ejemplo (Linux, UTF-8)

CSV reales que usan los programas de `ejemplos/`, los ejercicios de
`Ejercicios_Problemas/` y las pruebas del Corte 2. Todos en UTF-8
(el lector propio tolera BOM con `utf-8-sig`).

| Archivo | Filas | Columnas | Separador | Notas |
|---|---|---|---|---|
| `ventas.csv` | 12 | `fecha,ciudad,categoria,unidades,precio` | `,` | ciudades con tilde (Bogotá, Medellín); `fecha` es palabra reservada y vale como columna (D5) |
| `encuesta.csv` | 8 | `id;ciudad;edad;ingreso;fecha_ingreso` | `;` | trae un `ingreso` vacío (`nada`) y fechas `AAAA-MM-DD` para `convierta` |
| `empleados.csv` | 5 | `nombre,salario,ciudad` | `,` | salarios grandes para `invente`/`describa` |

Uso desde la raíz del proyecto:

```bash
python3 src/cli/main.py ejemplos/demo.arepa --ejecutar
```

```text
ventas = monte "datos/ventas.csv" con encabezado, separador ","
encuesta = monte "datos/encuesta.csv" con encabezado, separador ";"
```

Casos borde del lector propio (comillas, vacíos) viven en
`Ejercicios_Problemas/datos/` y `pruebas/datos/`.
