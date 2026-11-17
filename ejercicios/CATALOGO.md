# Catálogo de ejercicios resueltos

La ampliación añade **185 ejercicios** con enunciado, solución y resultados esperados.
El corpus de práctica contiene **349 programas** sin contar las pruebas positivas y negativas.

La ejecución final está documentada en el [reporte de verificación](REPORTE_AMPLIACION.md).

| Carpeta | Fáciles | Medianos | Difíciles | Adicionales | Total |
|---|---:|---:|---:|---:|---:|
| Corte 1 | 25 | 25 | 25 | 0 | 75 |
| Corte 2 | 25 | 25 | 25 | 75 de funciones | 150 |
| Corte 3 | 25 | 25 | 25 | 12 gráficas anteriores | 87 |
| Corte completo | — | — | — | 12 integradores y 25 sustentación | 37 |

## Cobertura

| Área | Ejemplos representativos |
|---|---|
| Léxico, sintaxis y operadores | Corte 1 y sustentación S01–S08 |
| Tablas, listas, registros, mutación y ciclos | Corte 2 y sustentación S09–S17 |
| CSV, tipos, limpieza, selección y filtros | Cortes 1–2 e integradores I01–I04 |
| Agrupación y estadísticas | Corte 2 y sustentación S19–S21 |
| Cinco gráficas, ejes, título y leyenda | Corte 3; D25 e I12 exportan las cinco |
| Regresión, perceptrón y árbol | Corte 3 D02–D04; integradores I05–I07 |
| Datos públicos y flujo reproducible | Integrador I12 y caso_estudio/programa.arepa |
| Diagnósticos y programas inválidos | ejercicios/pruebas/negativos y suites internas |

## Navegación

- [Corte 1](corte1/README.md)
- [Corte 2](corte2/README.md)
- [Corte 3](corte3/README.md)
- [Corte completo y sustentación](corte_completo/README.md)
- [Pruebas](pruebas/README.md)

## Verificar

```bash
python ejercicios/pruebas/ejecutar.py --ejercicios
python ejercicios/pruebas/ejecutar.py --completo
```

`--ejercicios` valida los 185 ejercicios añadidos, los 55 casos base y las
28 pruebas de diagnósticos, 23 de auditoría y cuatro de entrega reproducible.
`--completo` agrega los programas anteriores, los nueve ejemplos, el caso de estudio
y las diez suites internas. Los archivos se generan en carpetas temporales limpias.

Para conservar las salidas de una demostración, ejecutar un archivo individual:

```bash
python src/cli/main.py ejercicios/corte_completo/integradores/I12_pasajeros_publicos.arepa --ejecutar --sin-ventana
```
