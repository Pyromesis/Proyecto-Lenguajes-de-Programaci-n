# AREPA

AREPA (*Análisis Reproducible de datos Escrito con Palabras Autóctonas*) es
un lenguaje de dominio específico para preparar datos, calcular estadísticas,
generar gráficas y entrenar modelos mediante instrucciones en español.

Proyecto de Lenguajes de Programación y Transducción de la Universidad Sergio
Arboleda, 2026-2. Integrantes: Camilo Bernal, Diego Moreno y Yeisson Rincon.

El front-end utiliza ANTLR4. El equipo implementa las estructuras de datos,
el procesamiento CSV, la evaluación, el motor PNG y los modelos de aprendizaje
automático. El alcance académico está en el [enunciado](docs/Proyecto_LP.pdf).

## Instalación

Se requiere Python 3.11 o posterior. Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

El lexer y el parser generados están incluidos. Java 11 o posterior solo es
necesario para [regenerarlos](gramatica/README.md).

## Ejecutar un programa

```bash
python src/cli/main.py ejemplos/demo.arepa --ejecutar --sin-ventana
```

El siguiente programa carga ventas, calcula ingresos por ciudad y exporta
una tabla y una gráfica:

```text
quihubo
ventas = monte "datos/ventas.csv" con encabezado, separador ","
resumen = ventas
|> deje donde unidades > 0 y precio > 0
|> cree total = unidades * precio
|> junte por [ciudad]
|> resuma ingreso = sume(total), registros = cuente()

cuenteme resumen
pinte barras resumen
titulo "Ingresos por ciudad"
ejex ciudad
ejey ingreso
guardela "salidas/ingresos_ciudad.png"

guarde resumen como "salidas/resumen_ciudades.csv"
chao
```

Las rutas de datos y salidas se resuelven desde el directorio de ejecución.
Para empezar, consulte el [manual de usuario](docs/manuales/usuario.md).

## Opciones de consola

| Opción | Resultado |
|---|---|
| Sin opciones | Comprueba el análisis léxico y sintáctico del archivo |
| `--ejecutar` | Ejecuta el programa |
| `--sin-ventana` | Genera las gráficas sin abrir un visor |
| `--tokens` | Muestra los tokens |
| `--arbol` | Muestra el árbol de análisis |
| `--help`, `--ayuda` | Muestra la ayuda |
| `--version` | Muestra la versión |

Los diagnósticos indican la causa y la ubicación del problema. Algunas
operaciones, como dividir entre cero, producen un aviso y un valor especial
según las [reglas semánticas](docs/09_reglas_semanticas.md).

## Ejercicios y pruebas

Hay **349 ejercicios resueltos**: 75 del corte 1, 150 del corte 2,
87 del corte 3 y 37 integradores y propuestas de sustentación. Cada corte
incluye al menos 25 ejercicios por nivel de dificultad. El
[catálogo](ejercicios/CATALOGO.md) organiza su cobertura.

Para verificar los ejercicios, los nueve ejemplos, el caso de estudio y las
diez suites internas:

```bash
python ejercicios/pruebas/ejecutar.py --completo
```

Este modo reúne **469 pruebas del corredor y 370 pruebas internas**.
La [guía de pruebas](ejercicios/pruebas/README.md) explica los modos de
ejecución y las comprobaciones de resultados, errores, CSV y PNG.

Para incluir también la sincronización de gramática y la documentación:

```bash
python herramientas/verificar_entrega.py
```

Los resultados registrados y las correcciones verificadas se recogen en el
[informe de verificación técnica](docs/13_cierre_tecnico.md).

## Documentación

| Recurso | Contenido |
|---|---|
| [Índice de documentación](docs/README.md) | Especificación, informes y matrices por corte |
| [Manual de usuario](docs/manuales/usuario.md) | Instalación, sintaxis, gráficas y diagnóstico de errores |
| [Manual técnico](docs/manuales/tecnico.md) | Mantenimiento, regeneración y ampliación del intérprete |
| [Arquitectura](docs/05_arquitectura.md) | Algoritmos, módulos y trazabilidad con las pruebas |
| [Catálogo del lenguaje](docs/02_catalogo_instrucciones.md) | Instrucciones y palabras reservadas |
| [Guía de aprendizaje automático](docs/11_guia_machine_learning.md) | Preparación, modelos, métricas y evaluación |
| [Caso de estudio](caso_estudio/README.md) | Análisis reproducible de AirPassengers |
| [Ejercicios](ejercicios/README.md) | Programas resueltos por corte y dificultad |

## Organización

| Carpeta | Responsabilidad |
|---|---|
| `gramatica/`, `generado/` | Gramática y artefactos de ANTLR |
| `src/` | Intérprete, datos, modelos, gráficas y CLI |
| `datos/`, `ejemplos/` | Datos y programas de referencia |
| `ejercicios/`, `pruebas/` | Material de práctica y verificación |
| `caso_estudio/` | Análisis de un conjunto público |
| `docs/` | Documentación y enunciado |
| `herramientas/` | Chequeos, demostración y empaquetado |
| `salidas/` | Resultados CSV y PNG de los programas |

## Paquete de entrega

```bash
python herramientas/crear_entrega.py --probar
```

Genera un ZIP reproducible con manifiesto SHA-256 en `output/entregas/`,
instala sus dependencias en un entorno virtual nuevo y ejecuta la verificación.
Para comprobar un paquete existente:

```bash
python herramientas/crear_entrega.py --verificar output/entregas/arepa_entrega.zip
```
