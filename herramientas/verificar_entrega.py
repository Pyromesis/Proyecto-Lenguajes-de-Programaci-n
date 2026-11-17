"""Verificación técnica completa, válida tanto en Git como en una entrega ZIP."""
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]


def main():
    pasos = [
        "herramientas/chequeo_gramatica.py",
        "herramientas/chequeo_documentacion.py",
        "ejercicios/pruebas/ejecutar.py",
    ]
    for archivo in pasos:
        argumentos = [sys.executable, str(RAIZ / archivo)]
        if archivo.endswith("ejecutar.py"):
            argumentos.append("--completo")
        print("\nVerificando: " + archivo, flush=True)
        proceso = subprocess.run(argumentos, cwd=RAIZ, timeout=1200)
        if proceso.returncode:
            return proceso.returncode
    if (RAIZ / ".git").exists():
        proceso = subprocess.run(["git", "diff", "--check"], cwd=RAIZ, timeout=30)
        if proceso.returncode:
            return proceso.returncode
    print("\nVerificación técnica completa aprobada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
