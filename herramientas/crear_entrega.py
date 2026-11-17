"""Crea un ZIP reproducible de los archivos actuales, incluso los aún no confirmados.

Incluye fuentes, dependencias, datos, documentación, pruebas y evidencias.
No incluye .git, credenciales, entornos virtuales ni salidas temporales.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import venv
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = "MANIFIESTO_SHA256.json"
CARPETAS = ("src", "generado", "gramatica", "datos", "ejercicios", "pruebas",
            "docs", "ejemplos", "caso_estudio", "herramientas", ".github")
RAICES = ("README.md", ".gitignore", ".gitattributes", "requirements.txt", "generar_gramatica.sh")
EVIDENCIAS = ("README.md", ".gitkeep", "resumen_ciudades.csv", "resumen_ciclos.csv",
              "filtros_listos.csv", "regresion_casas.csv", "clasificacion_estudiantes.csv",
              "arbol_riesgo.csv", "memoria_resumen.csv")


def archivos_entrega(raiz=RAIZ):
    candidatos = [raiz / n for n in RAICES]
    candidatos += [raiz / "salidas" / n for n in EVIDENCIAS]
    for nombre in CARPETAS:
        candidatos.extend((raiz / nombre).rglob("*"))
    resultado = {}
    for archivo in candidatos:
        if not archivo.is_file() or archivo.is_symlink():
            continue
        relativo = archivo.relative_to(raiz)
        if any(p in ("__pycache__", ".venv", ".git") for p in relativo.parts):
            continue
        if archivo.suffix in (".pyc", ".pyo"):
            continue
        resultado[relativo.as_posix()] = archivo
    return dict(sorted(resultado.items()))


def crear_paquete(destino, raiz=RAIZ):
    destino = Path(destino)
    archivos = archivos_entrega(raiz)
    contenidos = {nombre: p.read_bytes() for nombre, p in archivos.items()}
    manifiesto = {"formato": 1, "archivos": {
        nombre: hashlib.sha256(datos).hexdigest() for nombre, datos in contenidos.items()}}
    contenidos[MANIFIESTO] = (json.dumps(manifiesto, ensure_ascii=False,
                                       sort_keys=True, indent=2) + "\n").encode("utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as salida:
        for nombre, datos in sorted(contenidos.items()):
            info = zipfile.ZipInfo(nombre, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            ejecutable = nombre.endswith(".sh") or nombre == "herramientas/consola/arepa"
            info.external_attr = (0o100755 if ejecutable else 0o100644) << 16
            salida.writestr(info, datos, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    verificar_paquete(destino)
    firma = hashlib.sha256(destino.read_bytes()).hexdigest()
    destino.with_suffix(destino.suffix + ".sha256").write_text(
        firma + "  " + destino.name + "\n", encoding="utf-8")
    return firma


def verificar_paquete(ruta):
    with zipfile.ZipFile(ruta) as paquete:
        nombres = paquete.namelist()
        if len(nombres) != len(set(nombres)):
            raise ValueError("El ZIP contiene rutas repetidas.")
        for nombre in nombres:
            partes = PurePosixPath(nombre)
            if partes.is_absolute() or ".." in partes.parts or "\\" in nombre or ":" in nombre:
                raise ValueError("El ZIP contiene una ruta no válida: " + nombre)
        manifiesto = json.loads(paquete.read(MANIFIESTO))
        archivos = manifiesto["archivos"]
        if manifiesto.get("formato") != 1 or set(nombres) != set(archivos) | {MANIFIESTO}:
            raise ValueError("El contenido del ZIP no coincide con su manifiesto.")
        for nombre, firma in archivos.items():
            if hashlib.sha256(paquete.read(nombre)).hexdigest() != firma:
                raise ValueError("El archivo no coincide con SHA-256: " + nombre)
        obligatorios = {"requirements.txt", "src/cli/main.py", "herramientas/verificar_entrega.py",
                        "ejercicios/resultados_esperados.json"}
        if not obligatorios.issubset(archivos):
            raise ValueError("La entrega no contiene todos los archivos obligatorios.")
        return len(archivos)


def probar_limpio(ruta):
    verificar_paquete(ruta)
    with tempfile.TemporaryDirectory(prefix="arepa_entrega_limpia_") as temporal:
        carpeta = Path(temporal)
        proyecto = carpeta / "proyecto"
        with zipfile.ZipFile(ruta) as paquete:
            paquete.extractall(proyecto)  # Las rutas se validaron antes de extraer.
        entorno = carpeta / "entorno"
        venv.EnvBuilder(with_pip=True).create(entorno)
        interprete = entorno / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run([str(interprete), "-m", "pip", "install", "-r",
                        str(proyecto / "requirements.txt")], check=True, timeout=300)
        subprocess.run([str(interprete), str(proyecto / "herramientas/verificar_entrega.py")],
                       cwd=proyecto, check=True, timeout=1200)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ / "output/entregas/arepa_entrega.zip")
    parser.add_argument("--verificar", type=Path, help="Comprueba un ZIP existente sin modificarlo")
    parser.add_argument("--probar", action="store_true", help="Instala y verifica el ZIP en un entorno virtual nuevo")
    opciones = parser.parse_args()
    try:
        if opciones.verificar:
            ruta = opciones.verificar
            print("Archivos verificados:", verificar_paquete(ruta))
        else:
            ruta = opciones.salida
            print("SHA-256:", crear_paquete(ruta))
            print("Entrega:", ruta)
        if opciones.probar:
            probar_limpio(ruta)
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as problema:
        print("No se pudo verificar la entrega:", problema, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
