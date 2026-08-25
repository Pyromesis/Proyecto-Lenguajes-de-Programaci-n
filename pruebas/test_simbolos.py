"""
AREPA - Pruebas unitarias de la tabla de símbolos y el contexto propio
----------------------------------------------------------------------
Prueba directamente src/runtime/simbolos.py y src/runtime/contexto.py:
declarar, consultar, actualizar, existencia, ámbitos, no declarados,
validación de identificadores, funciones 'invente' y registro de errores.

Uso:
    python pruebas/test_simbolos.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.tabla import Tabla  # noqa: E402
from errores_base import ErrorSemantico, ErrorVariable  # noqa: E402
from runtime.contexto import ContextoEjecucion, a_texto  # noqa: E402
from runtime.simbolos import FuncionArepa, TablaSimbolos  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


# ---------------------------------------------------------------------- #
# TablaSimbolos: declarar, consultar, actualizar
# ---------------------------------------------------------------------- #

@caso
def declarar_y_consultar():
    s = TablaSimbolos()
    s.declarar("ventas", 42)
    assert s.buscar("ventas") == 42


@caso
def actualizar_valor_existente():
    s = TablaSimbolos()
    s.declarar("x", 1)
    s.asignar("x", 2)
    assert s.buscar("x") == 2


@caso
def actualizar_inexistente_rechazado():
    s = TablaSimbolos()
    try:
        s.asignar("y", 1)
        raise AssertionError("asignar a un nombre no declarado debería fallar")
    except ErrorVariable as e:
        assert "no existe" in e.mensaje and "declarala" in e.mensaje


@caso
def consultar_inexistente_rechazado():
    s = TablaSimbolos()
    try:
        s.buscar("z")
        raise AssertionError("buscar un nombre no declarado debería fallar")
    except ErrorVariable as e:
        assert "no está declarada" in e.mensaje


# ---------------------------------------------------------------------- #
# Ámbitos encadenados (hijo ve al padre; el padre no ve al hijo)
# ---------------------------------------------------------------------- #

@caso
def hijo_ve_al_padre():
    padre = TablaSimbolos()
    padre.declarar("global", 10)
    hijo = padre.hijo()
    assert hijo.buscar("global") == 10
    assert hijo.existe("global") is True


@caso
def asignar_en_hijo_actualiza_al_padre():
    padre = TablaSimbolos()
    padre.declarar("contador", 0)
    hijo = padre.hijo()
    hijo.asignar("contador", 7)
    assert padre.buscar("contador") == 7


@caso
def declarar_en_hijo_no_afecta_al_padre():
    padre = TablaSimbolos()
    hijo = padre.hijo()
    hijo.declarar("local", 1)
    assert hijo.existe("local") is True
    assert padre.existe("local") is False
    assert padre.existe_local("local") is False
    assert hijo.existe_local("local") is True


@caso
def sombra_local_sobre_el_padre():
    padre = TablaSimbolos()
    padre.declarar("x", "padre")
    hijo = padre.hijo()
    hijo.declarar("x", "hijo")
    assert hijo.buscar("x") == "hijo"
    assert padre.buscar("x") == "padre"


@caso
def buscar_opcional_devuelve_none():
    s = TablaSimbolos()
    assert s.buscar_opcional("nadie") is None
    s.declarar("alguien", 5)
    assert s.buscar_opcional("alguien") == 5


# ---------------------------------------------------------------------- #
# Validación de identificadores (regla propia del DSL)
# ---------------------------------------------------------------------- #

@caso
def identificador_invalido_rechazado():
    s = TablaSimbolos()
    for malo in ("1abc", "mi variable", "a-b", ""):
        try:
            s.declarar(malo, 0)
            raise AssertionError("'{0}' debería rechazarse".format(malo))
        except ErrorSemantico:
            pass


@caso
def identificador_con_tilde_y_enn_valido():
    s = TablaSimbolos()
    s.declarar("año_fiscal", 2026)
    assert s.buscar("año_fiscal") == 2026


# ---------------------------------------------------------------------- #
# Funciones 'invente' guardadas como símbolos
# ---------------------------------------------------------------------- #

@caso
def funcion_se_guarda_como_simbolo():
    s = TablaSimbolos()
    funcion = FuncionArepa("doble", ["x"], None, s)
    s.declarar("doble", funcion)
    guardada = s.buscar("doble")
    assert isinstance(guardada, FuncionArepa)
    assert guardada.parametros == ["x"]
    assert "doble" in repr(guardada)


# ---------------------------------------------------------------------- #
# Contexto de ejecución: símbolos, salida, tablas y errores
# ---------------------------------------------------------------------- #

@caso
def contexto_reune_simbolos_salida_y_tablas():
    contexto = ContextoEjecucion()
    contexto.simbolos.declarar("tabla_demo", Tabla(["a"], nombre="demo"))
    contexto.imprimir("hola", 42)
    assert contexto.salida == ["hola 42"]
    assert isinstance(contexto.simbolos.buscar("tabla_demo"), Tabla)
    assert contexto.errores == []


@caso
def contexto_registra_errores():
    contexto = ContextoEjecucion()
    problema = ErrorVariable("La variable 'x' no está declarada.")
    contexto.registrar_error(problema)
    assert len(contexto.errores) == 1
    assert "no está declarada" in str(contexto.errores[0])


@caso
def a_texto_formatos_propios():
    assert a_texto(True) == "obvio"
    assert a_texto(False) == "falso"
    assert a_texto(4.0) == "4"
    assert a_texto("texto") == "texto"
    tabla = Tabla(["a", "b"], nombre="t")
    tabla.insertar_fila([1, "x"])
    assert "a" in a_texto(tabla) and "x" in a_texto(tabla)


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE LA TABLA DE SÍMBOLOS Y EL CONTEXTO PROPIO")
    print("=" * 78)
    for funcion in CASOS:
        try:
            funcion()
            pasaron += 1
            print("[PASÓ ] {0}".format(funcion.__name__))
        except AssertionError as problema:
            fallaron += 1
            print("[FALLÓ] {0}: {1}".format(funcion.__name__, problema))
        except Exception as problema:
            fallaron += 1
            print("[FALLÓ] {0}: excepción {1}".format(funcion.__name__, problema))
    print("-" * 78)
    print("Resultado: {0} de {1} pasaron".format(pasaron, len(CASOS)))
    return 0 if fallaron == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
