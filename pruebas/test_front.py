"""
AREPA - Pruebas del front-end (Fase 1)
--------------------------------------
Verifica que:
  * los programas de pruebas/positivos se reconozcan sin errores;
  * los programas de pruebas/negativos sean rechazados con un
    diagnóstico que incluya línea y columna;
  * los mensajes de error sean comprensibles (sin saltos crudos,
    sin volcados enormes y con pistas útiles);
  * la interfaz de línea de comandos responda con los códigos de
    salida correctos y con las opciones --tokens y --arbol.

Uso:
    python pruebas/test_front.py
"""

import glob
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.system("")  # habilita los colores ANSI en la consola de Windows

from lenguaje.analizador import analizar  # noqa: E402

VERDE = "\033[92m"
ROJO = "\033[91m"
GRIS = "\033[93m"
NEUTRO = "\033[0m"

LONGITUD_MAX_MENSAJE = 300


def mensajes_comprensibles(errores):
    """Revisa que ningún diagnóstico tenga saltos crudos ni sea un volcado."""
    for e in errores:
        m = e["mensaje"]
        if "\n" in m or "\r" in m:
            return False, "el mensaje contiene un salto de línea crudo"
        if len(m) > LONGITUD_MAX_MENSAJE:
            return False, "el mensaje es demasiado largo ({0} caracteres)".format(len(m))
    return True, ""


def probar_ruta(ruta, debe_fallar):
    with open(ruta, "r", encoding="utf-8-sig") as manejador:
        texto = manejador.read()
    _, _, errores = analizar(texto)

    if not debe_fallar:
        ok = len(errores) == 0
        detalle = "reconocido sin problemas" if ok else "{0} error(es)".format(len(errores))
        if ok:
            ok, razon = mensajes_comprensibles(errores)
            detalle = "reconocido sin problemas"
        return ok, detalle

    if len(errores) == 0:
        return False, "no fue detectado como inválido"

    ok_ubicacion = all(e["linea"] >= 1 and e["columna"] >= 0 for e in errores)
    if not ok_ubicacion:
        return False, "un error no reporta línea y columna válidas"

    ok_mensajes, razon = mensajes_comprensibles(errores)
    if not ok_mensajes:
        return False, razon

    # Caso especial: usar una reservada como variable debe explicarse
    if "reservada" in os.path.basename(ruta):
        if "palabra reservada" not in errores[0]["mensaje"]:
            return False, "no explica que se usó una palabra reservada"

    primero = errores[0]
    detalle = "rechazado: [{0}] L{1},C{2}: {3}".format(
        primero["tipo"], primero["linea"], primero["columna"], primero["mensaje"]
    )
    return True, detalle


def probar_cli():
    """Pruebas de integración sobre src/main.py (códigos de salida y flags)."""
    main_py = os.path.join(RAIZ, "src", "cli", "main.py")
    demo = os.path.join(RAIZ, "ejemplos", "demo.arepa")
    negativo = os.path.join(RAIZ, "pruebas", "negativos", "n01_falta_chao.arepa")
    casos = []

    def ejecutar(*args):
        return subprocess.run(
            [sys.executable, main_py] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    r = ejecutar(demo)
    casos.append(("CLI: programa válido sale con código 0", r.returncode == 0))
    r = ejecutar(demo)
    casos.append(("CLI: confirma que el programa está bien escrito", "bien escrito" in (r.stdout or "")))

    r = ejecutar(demo, "--arbol")
    casos.append(("CLI: --arbol imprime el árbol", "Árbol de análisis" in (r.stdout or "") and r.returncode == 0))

    r = ejecutar(demo, "--tokens")
    casos.append(("CLI: --tokens imprime la tabla de tokens", "TOKEN" in (r.stdout or "") and r.returncode == 0))

    r = ejecutar(negativo)
    casos.append(("CLI: programa inválido sale con código 1", r.returncode == 1))
    r = ejecutar(negativo)
    casos.append(("CLI: reporta la línea del error", "Línea" in (r.stdout or "")))

    r = ejecutar(os.path.join(RAIZ, "este_archivo_no_existe.arepa"))
    casos.append(("CLI: archivo inexistente sale con código 2", r.returncode == 2))

    return casos


def probar_diagnosticos():
    """Casos con aserción exacta de línea, columna y contenido del mensaje."""
    casos = []

    def diagnosticar(texto):
        _, _, errores = analizar(texto)
        return errores

    # 1. Error léxico: posición exacta del símbolo inválido
    errores = diagnosticar("quihubo\nx = 1 @ 2\nchao\n")
    assert len(errores) >= 1
    primero = errores[0]
    assert primero["tipo"] == "léxico"
    assert primero["linea"] == 2 and primero["columna"] == 6
    assert "@" in primero["mensaje"] and "no hace parte" in primero["mensaje"]
    casos.append(("diagnóstico: error léxico con línea y columna exactas", True))

    # 2. Error sintáctico en una línea avanzada se reporta en su línea
    errores = diagnosticar("quihubo\na = 1\nb = 2\nc = = 3\nchao\n")
    assert len(errores) >= 1
    assert errores[0]["linea"] == 4, "el error de la línea 4 se reportó en otra línea"
    casos.append(("diagnóstico: error en la línea 4 se reporta en la línea 4", True))

    # 3. Cadena sin cerrar: mensaje comprensible, no el texto técnico
    errores = diagnosticar('quihubo\nx = "sin cerrar\nchao\n')
    assert any("no hace parte" in e["mensaje"] for e in errores)
    assert not any("token recognition error" in e["mensaje"] for e in errores)
    casos.append(("diagnóstico: cadena sin cerrar en español", True))

    # 4. Palabra reservada usada como variable: el mensaje da una pista
    errores = diagnosticar("quihubo\nno = 5\nchao\n")
    assert any("palabra reservada" in e["mensaje"] for e in errores)
    casos.append(("diagnóstico: reservada como variable explica el problema", True))

    # 5. Delimitador faltante: el mensaje señala el '(' esperado
    errores = diagnosticar("quihubo\nfijese_si x > 1 { }\nchao\n")
    assert any("'('" in e["mensaje"] and "se esperaba" in e["mensaje"] for e in errores)
    casos.append(("diagnóstico: delimitador faltante señala el '(' esperado", True))

    # 6. 'chao' con basura después se rechaza (cierre incorrecto)
    errores = diagnosticar("quihubo\nx = 1\nchao chao\n")
    assert len(errores) >= 1
    casos.append(("diagnóstico: 'chao' con contenido extra se rechaza", True))

    # 7. Robustez: entradas malformadas no deben lanzar excepciones
    malformados = [
        "",
        "   ",
        "quihubo",
        "quihubo\n",
        "quihubo\nx =\nchao\n",
        "quihubo\nx = (((\nchao\n",
        "quihubo\npinte\nchao\n",
        "quihubo\nr = t |> escoja [\nchao\n",
        "quihubo\nfijese_si (obvio) { \nchao\n",
        'quihubo\nx = "abc\ny = \'def\nchao\n',
    ]
    for texto in malformados:
        _, _, errores = analizar(texto)  # no debe lanzar
    casos.append(("diagnóstico: 10 entradas malformadas sin excepciones", True))

    return casos


def main():
    casos = []
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "pruebas", "positivos", "*.arepa"))):
        casos.append((ruta, False))
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "pruebas", "negativos", "*.arepa"))):
        casos.append((ruta, True))

    positivas = sum(1 for _, d in casos if not d)
    negativas = sum(1 for _, d in casos if d)

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

    # --- Pruebas de diagnóstico (línea, columna y mensajes) ------------
    print("-" * 78)
    print(" Pruebas de diagnóstico")
    print("-" * 78)
    try:
        casos_diag = probar_diagnosticos()
    except AssertionError as problema:
        casos_diag = [("diagnóstico: suite completa", False)]
        print("fallo de diagnóstico: {0}".format(problema))
    except Exception as problema:
        casos_diag = [("diagnóstico: suite completa", False)]
        print("excepción inesperada en diagnósticos: {0}".format(problema))

    for nombre, ok in casos_diag:
        if ok:
            pasaron += 1
            print("{0}[PASÓ ]{1} {2}".format(VERDE, NEUTRO, nombre))
        else:
            fallaron += 1
            print("{0}[FALLÓ]{1} {2}".format(ROJO, NEUTRO, nombre))

    # --- Pruebas de la interfaz de línea de comandos -------------------
    print("-" * 78)
    print(" Pruebas de la interfaz (CLI)")
    print("-" * 78)
    try:
        casos_cli = probar_cli()
    except Exception as problema:
        casos_cli = [("CLI: suite de integración", False)]
        print("excepción inesperada en la suite CLI: {0}".format(problema))

    for nombre, ok in casos_cli:
        if ok:
            pasaron += 1
            print("{0}[PASÓ ]{1} {2}".format(VERDE, NEUTRO, nombre))
        else:
            fallaron += 1
            print("{0}[FALLÓ]{1} {2}".format(ROJO, NEUTRO, nombre))

    color_total = VERDE if fallaron == 0 else ROJO
    print("-" * 78)
    print(
        "Resultado: {0}{1} de {2} pruebas pasaron{3} "
        "({4} positivas + {5} negativas + {6} de diagnóstico + {7} de CLI)".format(
            color_total, pasaron, pasaron + fallaron, NEUTRO,
            positivas, negativas, len(casos_diag), len(casos_cli),
        )
    )
    if fallaron == 0:
        print("¡De una! El front-end quedó bacano.")
        return 0
    print("Uy, hubo tropiezos. Revisá los mensajes de arriba.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
