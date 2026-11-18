# Catálogo de ejercicios resueltos

El [índice general](README.md) contiene el inventario de los 349 programas
por corte y dificultad. Este catálogo organiza su cobertura temática.

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

## Verificación

Los modos de ejecución y las comprobaciones de resultados están en la
[guía de pruebas](pruebas/README.md). Para ejecutar un integrador y
conservar sus salidas:

```bash
python src/cli/main.py ejercicios/corte_completo/integradores/I12_pasajeros_publicos.arepa --ejecutar --sin-ventana
```
