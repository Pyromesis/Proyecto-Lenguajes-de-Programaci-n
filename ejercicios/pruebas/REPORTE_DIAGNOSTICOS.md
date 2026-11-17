# Verificación de diagnósticos de consola

Este reporte conserva la etapa de diagnósticos. La verificación técnica
posterior, incluida la auditoría adversarial, está en el
[cierre técnico](../../docs/13_cierre_tecnico.md).

Fecha: 17 de noviembre de 2026. Entorno: Windows, Python 3.13.14 y ANTLR
runtime 4.13.2.

## Resultados

```bash
python ejercicios/pruebas/test_diagnosticos.py
python ejercicios/pruebas/ejecutar.py --completo
```

- Suite específica: **28/28** pruebas aprobadas, con múltiples subcasos.
- Corredor completo: **442/442** pruebas aprobadas.
- Pruebas internas originales: **370/370**, en **10/10** suites.
- Ambos comandos terminaron con código **0**.
- También pasaron los verificadores de gramática y documentación, y
  `git diff --check`.

Los 28 contratos de diagnósticos están incluidos en todas las modalidades
del corredor: el modo predeterminado ejecuta 83 pruebas (55 base más 28 de
diagnósticos). El modo completo conserva la cobertura de los 349 ejercicios,
los nueve ejemplos y el caso de estudio.

## Comportamiento comprobado

1. Los 29 programas negativos muestran causa, ubicación disponible y una
   ayuda para corregir el problema, sin traceback de Python.
2. Los errores aritméticos señalan el operador; los de pipeline señalan la
   etapa que falla; las conversiones conservan la fila afectada.
3. Los errores en funciones conservan su origen y las llamadas. Los CSV
   distinguen el archivo fuente, el archivo de datos y la línea del CSV.
4. Se explican los archivos inexistentes, la fuente no UTF-8, destinos de
   guardado inválidos y argumentos incorrectos.
5. División por cero, módulo por cero, potencias de cero con exponente
   negativo y desbordamiento representado como infinito generan avisos.
   Mantienen los resultados definidos por AREPA y no detienen la ejecución.
6. Los avisos repetidos se agrupan por causa, ubicación y resultado. Se
   conserva un ejemplo de la fila afectada cuando existe contexto tabular.
   Los infinitos de signos distintos no comparten una explicación incorrecta.
7. No hay falsas alarmas en cálculos válidos, comentarios, cadenas, funciones
   no llamadas, ramas no ejecutadas, cero repeticiones, faltantes normales,
   fechas válidas ni operaciones permitidas sobre tablas vacías.
8. Los avisos no alteran `cuenteme`, `contexto.salida` ni los códigos de salida
   de programas válidos. Un aviso previo no oculta un error posterior.
9. La consola interactiva muestra ayudas al validar; un fallo al guardar no
   cierra la sesión ni borra el contenido.
10. Un fallo interno inesperado se identifica como interno, sin atribuirlo
    automáticamente al programa AREPA.

Los errores reales mantienen código 1; los problemas de argumentos o lectura
del programa usan código 2. Un programa válido, incluso con avisos, usa 0.

La descripción de uso está en el [manual de usuario](../../docs/manuales/usuario.md).
