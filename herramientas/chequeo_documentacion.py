#!/usr/bin/env python3
"""AREPA - Chequeo de documentación y estructura (Linux).

Comprueba:
* enlaces Markdown relativos que apunten a archivos inexistentes;
* rutas antiguas que quedaron de reorganizaciones;
* referencias `archivo.py::símbolo` con línea que ya no coinciden;
* conteo de ejercicios por corte y de ejemplos.
"""

from __future__ import annotations

import pathlib
import re
import sys
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
IGNORAR = {".git", ".venv", "generado", "__pycache__"}

RUTAS_VIEJAS = (
    "Ejercicios_Problemas",
    "manual_usuario.md",
    "manual_tecnico.md",
    "regresion_ejercicios.sh",
)

CONTEOS = {
    "ejercicios/corte1": 32,
    "ejercicios/corte2": 120,
    "ejercicios/corte3": 12,
    "ejemplos": 6,
}

ENLACE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REFERENCIA = re.compile(
    r"(?P<archivo>[A-Za-z0-9_./-]+\.py)::(?P<simbolo>[A-Za-z_][A-Za-z0-9_]*)"
    r"`?\s*(?:\((?P<linea>\d+)\)|\(línea\s+(?P<linea_texto>\d+)\))"
)


def archivos_markdown():
    for ruta in RAIZ.rglob("*.md"):
        if any(parte in IGNORAR for parte in ruta.parts):
            continue
        yield ruta


def revisar_enlaces():
    errores = []
    total = 0
    for md in archivos_markdown():
        texto = md.read_text(encoding="utf-8", errors="replace")
        for numero, linea in enumerate(texto.splitlines(), 1):
            for coincidencia in ENLACE.finditer(linea):
                destino = coincidencia.group(1).strip()
                if destino.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                destino = urllib.parse.unquote(destino.split("#", 1)[0])
                if not destino:
                    continue
                total += 1
                if not (md.parent / destino).exists():
                    errores.append(
                        "{0}:{1}: enlace roto -> {2}".format(
                            md.relative_to(RAIZ), numero, destino
                        )
                    )
    return total, errores


def _resolver_archivo(nombre):
    """Resuelve una ruta de .py citada, aunque el doc use solo el basename."""
    directa = RAIZ / nombre
    if directa.exists():
        return directa
    candidatos = [
        ruta
        for ruta in RAIZ.rglob(pathlib.Path(nombre).name)
        if not any(parte in IGNORAR for parte in ruta.parts)
    ]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def revisar_referencias():
    """Verifica referencias `archivo.py::símbolo` con su línea."""
    errores = []
    total = 0
    cache = {}
    for md in archivos_markdown():
        texto = md.read_text(encoding="utf-8", errors="replace")
        for numero, linea in enumerate(texto.splitlines(), 1):
            for coincidencia in REFERENCIA.finditer(linea):
                total += 1
                archivo = coincidencia.group("archivo")
                simbolo = coincidencia.group("simbolo")
                linea_ref = int(
                    coincidencia.group("linea") or coincidencia.group("linea_texto")
                )
                if archivo not in cache:
                    cache[archivo] = _resolver_archivo(archivo)
                ruta = cache[archivo]
                if ruta is None:
                    errores.append(
                        "{0}:{1}: no pude resolver {2}".format(
                            md.relative_to(RAIZ), numero, archivo
                        )
                    )
                    continue
                lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
                if not (1 <= linea_ref <= len(lineas)) or simbolo not in lineas[linea_ref - 1]:
                    contenido = (
                        lineas[linea_ref - 1].strip()[:70]
                        if 1 <= linea_ref <= len(lineas)
                        else "fuera de rango"
                    )
                    errores.append(
                        "{0}:{1}: {2}::{3} (línea {4}) no coincide: {5}".format(
                            md.relative_to(RAIZ),
                            numero,
                            archivo,
                            simbolo,
                            linea_ref,
                            contenido,
                        )
                    )
    return total, errores


def revisar_rutas_viejas():
    errores = []
    for md in archivos_markdown():
        texto = md.read_text(encoding="utf-8", errors="replace")
        for vieja in RUTAS_VIEJAS:
            if vieja in texto:
                errores.append(
                    "{0}: contiene la ruta antigua {1}".format(
                        md.relative_to(RAIZ), vieja
                    )
                )
    return errores


def revisar_conteos():
    errores = []
    for carpeta, esperado in CONTEOS.items():
        obtenido = len(list((RAIZ / carpeta).rglob("*.arepa")))
        if obtenido != esperado:
            errores.append(
                "{0}: {1} .arepa (esperados {2})".format(carpeta, obtenido, esperado)
            )
    return errores


def main():
    total_enlaces, errores_enlaces = revisar_enlaces()
    total_refs, errores_refs = revisar_referencias()
    errores = (
        errores_enlaces
        + errores_refs
        + revisar_rutas_viejas()
        + revisar_conteos()
    )
    if errores:
        print("Documentación y estructura con problemas:")
        for error in errores:
            print("  - {0}".format(error))
        return 1
    print(
        "Documentación y estructura: {0} enlaces relativos, "
        "{1} referencias de código, 0 rutas antiguas, "
        "conteos 32/120/12/6.".format(total_enlaces, total_refs)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
