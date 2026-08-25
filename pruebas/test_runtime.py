"""
AREPA - Pruebas del runtime propio (src/runtime)
------------------------------------------------
Ejecuta programas completos del DSL con el ejecutor propio y verifica:
asignaciones, carga CSV, selección, filtrado, columnas calculadas,
agregaciones, funciones, condicionales, guardado y errores semánticos.

Uso:
    python pruebas/test_runtime.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.tabla import Tabla  # noqa: E402
from datos.tipos import NADA  # noqa: E402
from errores_base import ErrorArepa  # noqa: E402
from lenguaje.analizador import analizar  # noqa: E402
from runtime.ejecutor import EjecutorArepa  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


def correr(programa):
    """Parsea y ejecuta un programa; devuelve el ejecutor."""
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa no parseó: {0}".format(errores)
    ejecutor = EjecutorArepa()
    ejecutor.ejecutar(arbol)
    return ejecutor


def correr_y_fallar(programa):
    """Ejecuta un programa que debe fallar; devuelve el error."""
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa debería fallar en ejecución, no en parseo"
    try:
        EjecutorArepa().ejecutar(arbol)
    except ErrorArepa as problema:
        return problema
    raise AssertionError("el programa debería haber fallado: " + programa)


RUTA_VENTAS = os.path.join(RAIZ, "datos", "ventas.csv").replace("\\", "/")
RUTA_ENCUESTA = os.path.join(RAIZ, "datos", "encuesta.csv").replace("\\", "/")


# ---------------------------------------------------------------------- #
# Asignaciones y variables
# ---------------------------------------------------------------------- #

@caso
def asignaciones_y_reasignacion():
    ejecutor = correr("quihubo\nx = 5\nx = x + 1\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("x") == 6


@caso
def variable_inexistente_rechazada():
    problema = correr_y_fallar("quihubo\nw = z + 1\nchao\n")
    assert "no existe ni como columna ni como variable" in problema.mensaje


# ---------------------------------------------------------------------- #
# Carga, selección y filtrado con CSV real
# ---------------------------------------------------------------------- #

@caso
def monte_carga_csv_real():
    programa = 'quihubo\nventas = monte "{0}" con encabezado\nchao\n'.format(RUTA_VENTAS)
    ejecutor = correr(programa)
    tabla = ejecutor.contexto.simbolos.buscar("ventas")
    assert isinstance(tabla, Tabla)
    assert tabla.num_filas == 12
    assert tabla.nombres_columnas == ["fecha", "ciudad", "categoria", "unidades", "precio"]


@caso
def monte_con_archivo_inexistente():
    problema = correr_y_fallar('quihubo\nt = monte "datos/nunca.csv"\nchao\n')
    assert "No encontré el archivo" in problema.mensaje


@caso
def escoja_selecciona_columnas():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "pocas = ventas |> escoja [ciudad, unidades]\nchao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    tabla = ejecutor.contexto.simbolos.buscar("pocas")
    assert tabla.nombres_columnas == ["ciudad", "unidades"]


@caso
def escoja_columna_inexistente():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "pocas = ventas |> escoja [no_existe]\nchao\n".format(RUTA_VENTAS)
    )
    problema = correr_y_fallar(programa)
    assert "no existe" in problema.mensaje and "disponibles" in problema.mensaje


@caso
def deje_donde_filtra_filas():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "grandes = ventas |> deje donde unidades > 12\nchao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    tabla = ejecutor.contexto.simbolos.buscar("grandes")
    assert tabla.num_filas == 6  # 20, 15, 30, 25, 18 y 14
    assert min(tabla.valores_columna("unidades")) > 12


@caso
def deje_con_nada_descarta_la_fila():
    programa = (
        'quihubo\nt = monte "{0}" con encabezado, separador ";"\n'
        "r = t |> deje donde ingreso > 0\nchao\n".format(RUTA_ENCUESTA)
    )
    ejecutor = correr(programa)
    # 8 filas; la fila 3 tiene ingreso vacío (nada) y se descarta
    assert ejecutor.contexto.simbolos.buscar("r").num_filas == 7


@caso
def pipeline_completo_con_cree():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "con_total = ventas\n"
        "|> escoja [ciudad, unidades, precio]\n"
        "|> deje donde unidades > 0 y precio > 0\n"
        "|> cree total = unidades * precio\n"
        "chao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    tabla = ejecutor.contexto.simbolos.buscar("con_total")
    assert "total" in tabla.nombres_columnas
    assert tabla.filas[0].valor_en(3) == 12 * 3500


@caso
def operacion_sin_tabla_de_entrada_rechazada():
    problema = correr_y_fallar("quihubo\nr = escoja [a]\nchao\n")
    assert "necesita una tabla de entrada" in problema.mensaje


# ---------------------------------------------------------------------- #
# Orden, limpieza y conversión
# ---------------------------------------------------------------------- #

@caso
def acomode_orden_descendente():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "ordenadas = ventas |> acomode por [unidades] pa_abajo\nchao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    unidades = ejecutor.contexto.simbolos.buscar("ordenadas").valores_columna("unidades")
    assert unidades == sorted(unidades, reverse=True)


@caso
def limpie_duplicados_y_vacios():
    programa = (
        'quihubo\nt = monte "{0}" con encabezado, separador ";"\n'
        "limpia = t |> limpie duplicados\n"
        "sin_vacios = t |> limpie vacios\n"
        "rellena = t |> limpie vacios con 0\n"
        "chao\n".format(RUTA_ENCUESTA)
    )
    ejecutor = correr(programa)
    assert ejecutor.contexto.simbolos.buscar("rellena").num_filas == 8
    assert ejecutor.contexto.simbolos.buscar("sin_vacios").num_filas == 7


@caso
def convierta_tipo_de_columna():
    programa = (
        'quihubo\nt = monte "{0}" con encabezado\n'
        "fechas = t |> convierta fecha -> fecha\nchao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    assert ejecutor.contexto.simbolos.buscar("fechas") is not None


# ---------------------------------------------------------------------- #
# Agrupamiento y agregaciones propias
# ---------------------------------------------------------------------- #

@caso
def junte_resuma_agregaciones():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "resumen = ventas\n"
        "|> junte por [ciudad]\n"
        "|> resuma ingreso = sume(unidades), registros = cuente()\n"
        "chao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    resumen = ejecutor.contexto.simbolos.buscar("resumen")
    assert resumen.nombres_columnas == ["ciudad", "ingreso", "registros"]
    por_ciudad = dict(
        (f.valor_en(0), (f.valor_en(1), f.valor_en(2))) for f in resumen.filas
    )
    bogota_ingreso, bogota_registros = por_ciudad["Bogotá"]
    assert bogota_registros == 5
    assert bogota_ingreso == 12 + 15 + 6 + 18 + 9


@caso
def agregaciones_estadisticas_propias():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "r = ventas |> resuma p = promedie(precio), m = mediana(unidades), "
        "mx = maximo(precio), d = desviacion(precio)\n"
        "chao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    fila = ejecutor.contexto.simbolos.buscar("r").filas[0]
    precios = [3500, 3200, 4100, 4100, 3600, 2200, 2300, 2400, 3300, 3400, 4250, 4150]
    promedio = sum(precios) / len(precios)
    assert abs(fila.valor_en(0) - promedio) < 1e-9
    assert fila.valor_en(2) == max(precios)


@caso
def agregacion_fuera_de_resuma_rechazada():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "x = sume(unidades)\nchao\n".format(RUTA_VENTAS)
    )
    problema = correr_y_fallar(programa)
    assert "solo puede usarse dentro de 'resuma'" in problema.mensaje


@caso
def agregacion_sobre_columna_inexistente():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "r = ventas |> resuma s = sume(no_existe)\nchao\n".format(RUTA_VENTAS)
    )
    problema = correr_y_fallar(programa)
    assert "no existe" in problema.mensaje


# ---------------------------------------------------------------------- #
# Funciones, condicionales y salida
# ---------------------------------------------------------------------- #

@caso
def invente_devuelva_y_recursion():
    programa = (
        "quihubo\n"
        "invente factorial(n) {\n"
        "    fijese_si (n <= 1) {\n"
        "        devuelva 1\n"
        "    }\n"
        "    devuelva n * factorial(n - 1)\n"
        "}\n"
        "f = factorial(5)\n"
        "chao\n"
    )
    ejecutor = correr(programa)
    assert ejecutor.contexto.simbolos.buscar("f") == 120


@caso
def funcion_con_parametros_incorrectos():
    programa = (
        "quihubo\n"
        "invente doble(x) { devuelva x * 2 }\n"
        "r = doble(1, 2)\n"
        "chao\n"
    )
    problema = correr_y_fallar(programa)
    assert "recibe 1 parametro(s)" in problema.mensaje


@caso
def funcion_inexistente_rechazada():
    problema = correr_y_fallar("quihubo\nr = volar(3)\nchao\n")
    assert "no existe" in problema.mensaje and "invente" in problema.mensaje


@caso
def fijese_si_condicion_no_logica_rechazada():
    problema = correr_y_fallar("quihubo\nfijese_si (5) { }\nchao\n")
    assert "obvio o falso" in problema.mensaje


@caso
def cuenteme_acumula_salida():
    ejecutor = correr('quihubo\ncuenteme "hola", 42, obvio, nada\nchao\n')
    assert ejecutor.contexto.salida == ["hola 42 obvio nada"]


@caso
def describa_produce_resumen_propio():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "describa ventas\nchao\n".format(RUTA_VENTAS)
    )
    ejecutor = correr(programa)
    texto = "\n".join(ejecutor.contexto.salida)
    assert "promedie" in texto and "mediana" in texto and "desviacion" in texto


# ---------------------------------------------------------------------- #
# Guardado con el escritor propio
# ---------------------------------------------------------------------- #

@caso
def guarde_escribe_csv_legible():
    salida = os.path.join(RAIZ, "salidas", "prueba_guarde.csv").replace("\\", "/")
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "pocas = ventas |> escoja [ciudad, unidades]\n"
        'guarde pocas como "{1}"\n'
        "chao\n".format(RUTA_VENTAS, salida)
    )
    ejecutor = correr(programa)
    assert any("guarde" in linea for linea in ejecutor.contexto.salida)
    from datos.lector_csv import LectorCSV

    releida = LectorCSV().leer(salida, "releida")
    assert releida.num_filas == 12
    assert releida.nombres_columnas == ["ciudad", "unidades"]


@caso
def guarde_sobre_variable_no_tabla_rechazado():
    programa = 'quihubo\nx = 5\nguarde x como "salidas/x.csv"\nchao\n'
    problema = correr_y_fallar(programa)
    assert "no es una tabla" in problema.mensaje


@caso
def pinte_valida_columnas_de_la_grafica():
    programa = (
        'quihubo\nventas = monte "{0}" con encabezado\n'
        "pinte barras ventas\n titulo \"T\"\n ejex ciudad\n ejey no_existe\n"
        "chao\n".format(RUTA_VENTAS)
    )
    problema = correr_y_fallar(programa)
    assert "no existe" in problema.mensaje


@caso
def devuelva_fuera_de_funcion_rechazado():
    problema = correr_y_fallar("quihubo\ndevuelva 5\nchao\n")
    assert "dentro de una función" in problema.mensaje


# ---------------------------------------------------------------------- #
# CSV "duro": comillas, separadores y valores faltantes
# ---------------------------------------------------------------------- #

@caso
def csv_duro_se_carga_completo():
    ruta = os.path.join(RAIZ, "pruebas", "datos", "duro.csv").replace("\\", "/")
    ejecutor = correr('quihubo\nt = monte "{0}" con encabezado\nchao\n'.format(ruta))
    tabla = ejecutor.contexto.simbolos.buscar("t")
    assert tabla.num_filas == 4
    assert tabla.filas[1].valor_en(1) == "6.500,25"
    assert tabla.filas[2].valor_en(1) == 'con "extras"'
    assert tabla.filas[3].valor_en(2) is NADA


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DEL RUNTIME PROPIO")
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

