"""
AREPA - Pruebas del front-end (Fase 1)
--------------------------------------
Verifica que:
  * los programas de pruebas/positivos se reconozcan sin errores;
  * los programas de pruebas/negativos sean rechazados con un
    diagnóstico que incluya línea y columna.

Uso:
    python pruebas/test_front.py
"""

import glob
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.system("")  # habilita los colores ANSI en la consola de Windows

from main import analizar  # noqa: E402

VERDE = "\033[92m"
ROJO = "\033[91m"
GRIS = "\033[93m"
NEUTRO = "\033[0m"


def probar_ruta(ruta, debe_fallar):
    with open(ruta, "r", encoding="utf-8-sig") as manejador:
        texto = manejador.read()
    _, _, errores = analizar(texto)

    if not debe_fallar:
        ok = len(errores) == 0
        detalle = "reconocido sin problemas" if ok else "{0} error(es)".format(len(errores))
    else:
        ok = len(errores) > 0 and all(
            e["linea"] >= 1 and e["columna"] >= 0 for e in errores
        )
        if ok:
            primero = errores[0]
            detalle = "rechazado: [{0}] L{1},C{2}: {3}".format(
                primero["tipo"], primero["linea"], primero["columna"], primero["mensaje"]
            )
        else:
            detalle = "no fue detectado como inválido"

    return ok, detalle


def main():
    casos = []
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "pruebas", "positivos", "*.arepa"))):
        casos.append((ruta, False))
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "pruebas", "negativos", "*.arepa"))):
        casos.append((ruta, True))

    pasaron = 0
    fallaron = 0

    print("=" * 78)
    print(" PRUEBAS DEL FRONT-END AREPA")
    print("=" * 78)

    for ruta, debe_fallar in casos:
        nombre = os.path.basename(ruta)
        clase = "POSITIVA" if not debe_fallar else "NEGATIVA"
        try:
            ok, detalle = probar_ruta(ruta, debe_fallar)
        except Exception as problema:
            ok, detalle = False, "excepción inesperada: {0}".format(problema)

        if ok:
            pasaron += 1
            color = VERDE
            marca = "PASÓ "
        else:
            fallaron += 1
            color = ROJO
            marca = "FALLÓ"

        print("{0}[{1}]{2} ({3}) {4}: {5}".format(color, marca, NEUTRO, clase, nombre, detalle))

    color_total = VERDE if fallaron == 0 else ROJO
    print("-" * 78)
    print(
        "Resultado: {0}{1} de {2} pruebas pasaron{3} "
        "(4 positivas esperadas + 10 negativas esperadas)".format(
            color_total, pasaron, len(casos), NEUTRO
        )
    )
    if fallaron == 0:
        print("¡De una! El front-end quedó bacano.")
        return 0
    print("Uy, hubo tropiezos. Revisá los mensajes de arriba.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
