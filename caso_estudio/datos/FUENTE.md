# Fuente del conjunto de datos

## Origen

`pasajeros.csv` contiene la serie mensual **AirPassengers**: número de
pasajeros internacionales (en miles) transportados por una aerolínea entre
enero de 1949 y diciembre de 1960.

- Dataset clásico de series de tiempo, publicado originalmente en:
  Box, G. E. P.; Jenkins, G. M.; Reinsel, G. C.; Ljung, G. M.
  *Time Series Analysis: Forecasting and Control*. 5.ª ed., Wiley, 2015.
- Copia descargada (formato original `Month,Passengers`):
  <https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv>
- Fecha de descarga: 2026-10-21.
- Los valores son datos factuales de dominio público; se cita la fuente
  bibliográfica por trazabilidad académica.

## Transformación aplicada

El archivo original trae dos columnas: `Month` (texto `AAAA-MM`) y
`Passengers` (entero). Para que el DSL trabaje con columnas numéricas y pueda
construir un eje temporal continuo, se separó el mes y se renombraron las
columnas:

| Original | Local |
|---|---|
| `Month` = `1949-01` | `anio` = `1949`, `mes` = `1` |
| `Passengers` = `112` | `pasajeros` = `112` |

No se eliminaron ni imputaron filas: las 144 observaciones están completas.

## Integridad

```text
SHA-256  caso_estudio/datos/pasajeros.csv
4fb41b8c01879e8badd175a968a7f6695d7b67bf4a6831cdb1880a2564b0c014
```

Verificación:

```bash
sha256sum caso_estudio/datos/pasajeros.csv
wc -l caso_estudio/datos/pasajeros.csv   # 145 líneas = encabezado + 144 datos
```

## Cifras de control

| Métrica | Valor |
|---|---:|
| Observaciones | 144 |
| Suma de pasajeros | 40 363 |
| Promedio mensual | 280.2986 |
| Mínimo | 104 (noviembre de 1949) |
| Máximo | 622 (julio de 1960) |
| Total 1949 | 1 520 |
| Total 1960 | 5 714 |
