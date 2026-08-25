"""
AREPA - Pruebas de la biblioteca propia de datos (src/datos)
------------------------------------------------------------
Verifica el lector CSV propio, la Tabla propia y el sistema de tipos
propio. Ninguna prueba usa csv/pandas: se prueba exclusivamente el
código del equipo.

Uso:
    python pruebas/test_datos.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.escritor_csv import EscritorCSV  # noqa: E402
from datos.lector_csv import LectorCSV  # noqa: E402
from datos.tabla import Tabla  # noqa: E402
from datos.tipos import NADA, convertir_a_tipo, texto_a_valor  # noqa: E402
from errores_base import ErrorColumna, ErrorCSV, ErrorTipos  # noqa: E402

CASOS = []


def caso(funcion):
    CASOS.append(funcion)
    return funcion


# ---------------------------------------------------------------------- #
# Lector CSV propio
# ---------------------------------------------------------------------- #

@caso
def csv_valido_basico():
    tabla = LectorCSV().leer_texto("a,b\n1,x\n2,y\n", "t")
    assert tabla.nombres_columnas == ["a", "b"]
    assert tabla.num_filas == 2
    assert tabla.filas[0].valores == [1, "x"]
    assert tabla.filas[1].valores == [2, "y"]


@caso
def csv_vacio_rechazado():
    try:
        LectorCSV().leer_texto("")
        raise AssertionError("un CSV vacío debería rechazarse")
    except ErrorCSV as e:
        assert "vacío" in e.mensaje


@caso
def csv_solo_encabezados():
    tabla = LectorCSV().leer_texto("a,b,c\n", "t")
    assert tabla.nombres_columnas == ["a", "b", "c"]
    assert tabla.num_filas == 0


@caso
def csv_valores_faltantes_se_rellenan_con_nada():
    tabla = LectorCSV().leer_texto("a,b,c\n1,2\n3\n", "t")
    assert tabla.filas[0].valores == [1, 2, NADA]
    assert tabla.filas[1].valores == [3, NADA, NADA]


@caso
def csv_comillas_protegen_el_separador():
    tabla = LectorCSV().leer_texto('nombre,nota\n"García, Ana",5\n', "t")
    assert tabla.filas[0].valores == ["García, Ana", 5]


@caso
def csv_comillas_escapadas():
    tabla = LectorCSV().leer_texto('frase\n"dijo ""hola"""\n', "t")
    assert tabla.filas[0].valores == ['dijo "hola"']


@caso
def csv_separador_personalizado():
    tabla = LectorCSV(separador=";").leer_texto("a;b\n1;2\n", "t")
    assert tabla.filas[0].valores == [1, 2]


@caso
def csv_lineas_vacias_se_ignoran():
    tabla = LectorCSV().leer_texto("a\n\n1\n\n\n2\n", "t")
    assert tabla.num_filas == 2


@caso
def csv_sin_encabezado():
    tabla = LectorCSV(con_encabezado=False).leer_texto("1,2\n3,4\n", "t")
    assert tabla.nombres_columnas == ["columna_1", "columna_2"]
    assert tabla.num_filas == 2


@caso
def csv_demasiados_campos_rechazado():
    try:
        LectorCSV().leer_texto("a,b\n1,2,3\n", "t")
        raise AssertionError("una fila más ancha que el encabezado debería fallar")
    except ErrorCSV as e:
        assert "3 campos" in e.mensaje


@caso
def csv_comillas_sin_cerrar_rechazado():
    try:
        LectorCSV().leer_texto('a\n"sin cerrar\n', "t")
        raise AssertionError("las comillas sin cerrar deberían fallar")
    except ErrorCSV as e:
        assert "sin cerrar" in e.mensaje


@caso
def csv_archivo_inexistente():
    try:
        LectorCSV().leer(os.path.join(RAIZ, "no_existe_nunca.csv"))
        raise AssertionError("un archivo inexistente debería fallar")
    except AssertionError:
        raise
    except Exception as e:
        assert "No encontré el archivo" in str(e)


@caso
def csv_archivo_real_del_proyecto():
    ruta = os.path.join(RAIZ, "datos", "ventas.csv")
    tabla = LectorCSV().leer(ruta, "ventas")
    assert tabla.nombres_columnas == ["fecha", "ciudad", "categoria", "unidades", "precio"]
    assert tabla.num_filas == 12
    assert tabla.filas[0].valor_en(0) == "2026-01-05"


@caso
def csv_archivo_con_separador_punto_y_coma():
    ruta = os.path.join(RAIZ, "datos", "encuesta.csv")
    tabla = LectorCSV(separador=";").leer(ruta, "encuesta")
    assert tabla.num_filas == 8
    # la fila 3 tiene ingreso vacío -> nada
    assert tabla.filas[2].valor_en(3) is NADA


# ---------------------------------------------------------------------- #
# Tipos propios
# ---------------------------------------------------------------------- #

@caso
def tipos_conversion_de_texto_csv():
    assert texto_a_valor("42") == 42
    assert texto_a_valor("3.14") == 3.14
    assert texto_a_valor("obvio") is True
    assert texto_a_valor("falso") is False
    assert texto_a_valor("") is NADA
    assert texto_a_valor("hola") == "hola"


@caso
def tipos_convierta_numero():
    assert convertir_a_tipo("42", "numero") == 42
    assert convertir_a_tipo("3.5", "numero") == 3.5
    assert convertir_a_tipo(NADA, "numero") is NADA


@caso
def tipos_conversion_imposible_lanza_error():
    try:
        convertir_a_tipo("abc", "numero")
        raise AssertionError("'abc' a numero debería fallar")
    except ErrorTipos as e:
        assert "No pude convertir" in e.mensaje


@caso
def tipos_fecha_valida_propia():
    assert convertir_a_tipo("2026-02-28", "fecha") == "2026-02-28"
    assert convertir_a_tipo("2024-02-29", "fecha") == "2024-02-29"  # bisiesto
    try:
        convertir_a_tipo("2026-02-30", "fecha")
        raise AssertionError("30 de febrero debería fallar")
    except ErrorTipos:
        pass
    try:
        convertir_a_tipo("2026-13-01", "fecha")
        raise AssertionError("mes 13 debería fallar")
    except ErrorTipos:
        pass


# ---------------------------------------------------------------------- #
# Tabla propia
# ---------------------------------------------------------------------- #

def _tabla_demo():
    return LectorCSV().leer_texto(
        "ciudad,unidades,precio\n"
        "Bogotá,10,2000\n"
        "Cali,5,3000\n"
        "Bogotá,8,2500\n"
        "Medellín,1,9999\n",
        "demo",
    )


@caso
def tabla_seleccion_de_columnas():
    resultado = _tabla_demo().seleccionar(["unidades", "ciudad"])
    assert resultado.nombres_columnas == ["unidades", "ciudad"]
    assert resultado.filas[0].valores == [10, "Bogotá"]


@caso
def tabla_seleccion_columna_inexistente():
    try:
        _tabla_demo().seleccionar(["no_existe"])
        raise AssertionError("debería fallar por columna inexistente")
    except ErrorColumna as e:
        assert "no existe" in e.mensaje and "disponibles" in e.mensaje


@caso
def tabla_filtrado():
    tabla = _tabla_demo()
    indice = tabla.indice_columna("unidades")
    resultado = tabla.filtrar(lambda f: f.valor_en(indice) > 6)
    assert resultado.num_filas == 2  # 10 y 8


@caso
def tabla_ordenamiento_propio_ascendente():
    resultado = _tabla_demo().ordenar([("unidades", "pa_arriba")])
    unidades = resultado.valores_columna("unidades")
    assert unidades == [1, 5, 8, 10]


@caso
def tabla_ordenamiento_propio_descendente():
    resultado = _tabla_demo().ordenar([("unidades", "pa_abajo")])
    assert resultado.valores_columna("unidades") == [10, 8, 5, 1]


@caso
def tabla_ordenamiento_estable_por_dos_claves():
    tabla = LectorCSV().leer_texto(
        "g,n\nA,2\nB,1\nA,1\nB,2\nA,1\n", "t"
    )
    resultado = tabla.ordenar([("g", "pa_arriba"), ("n", "pa_abajo")])
    pares = list(zip(resultado.valores_columna("g"), resultado.valores_columna("n")))
    assert pares == [("A", 2), ("A", 1), ("A", 1), ("B", 2), ("B", 1)]


@caso
def tabla_ordenamiento_coloca_nada_al_final():
    # el 'nada' viene de un campo faltante en la segunda fila
    tabla = LectorCSV().leer_texto("a,x\n5,3\n4,\n6,1\n", "t")
    resultado = tabla.ordenar([("x", "pa_arriba")])
    assert resultado.valores_columna("x") == [1, 3, NADA]


@caso
def tabla_crear_columna_calculada():
    tabla = _tabla_demo()
    indice_u = tabla.indice_columna("unidades")
    indice_p = tabla.indice_columna("precio")
    tabla.crear_columna("total", lambda f: f.valor_en(indice_u) * f.valor_en(indice_p))
    assert "total" in tabla.nombres_columnas
    assert tabla.filas[0].valor_en(3) == 20000


@caso
def tabla_crear_columna_repetida_rechazada():
    try:
        _tabla_demo().crear_columna("ciudad", lambda f: 1)
        raise AssertionError("crear una columna existente debería fallar")
    except ErrorColumna:
        pass


@caso
def tabla_renombrar():
    tabla = _tabla_demo()
    tabla.renombrar("unidades", "cantidad")
    assert "cantidad" in tabla.nombres_columnas and "unidades" not in tabla.nombres_columnas


@caso
def tabla_quitar_duplicados_conserva_primera():
    tabla = LectorCSV().leer_texto("a,b\n1,x\n1,x\n2,y\n1,x\n", "t")
    tabla.quitar_duplicados()
    assert tabla.num_filas == 2


@caso
def tabla_rellenar_vacios():
    tabla = LectorCSV().leer_texto("a,b\n1,\n2,5\n", "t")
    tabla.rellenar_vacios(0)
    assert tabla.filas[0].valores == [1, 0]


@caso
def tabla_eliminar_filas_con_vacios():
    tabla = LectorCSV().leer_texto("a,b\n1,\n2,5\n,7\n", "t")
    tabla.eliminar_filas_con_vacios()
    assert tabla.num_filas == 1


@caso
def tabla_conversion_de_columna():
    tabla = LectorCSV().leer_texto("x\n1\n2\n", "t")
    tabla.convertir_columna("x", "texto", lambda v, ctx: convertir_a_tipo(v, "texto", ctx))
    assert tabla.valores_columna("x") == ["1", "2"]


@caso
def tabla_agrupar_propio():
    grupos = _tabla_demo().agrupar(["ciudad"])
    claves = [clave for clave, _ in grupos]
    assert claves == [("Bogotá",), ("Cali",), ("Medellín",)]  # orden de aparición
    assert grupos[0][1].__len__() == 2


@caso
def tabla_texto_formato_propio():
    texto = _tabla_demo().texto_tabla()
    assert "ciudad" in texto and "Bogotá" in texto


# ---------------------------------------------------------------------- #
# Escritor CSV propio
# ---------------------------------------------------------------------- #

@caso
def escritor_csv_roundtrip():
    tabla = LectorCSV().leer_texto('a,b\n1,"x,y"\n2,"di ""hola"""\n', "t")
    ruta = os.path.join(RAIZ, "salidas", "prueba_escritor.csv")
    EscritorCSV().escribir(ruta, tabla)
    leido = LectorCSV().leer(ruta, "releido")
    assert leido.filas[0].valores == [1, "x,y"]
    assert leido.filas[1].valores == [2, 'di "hola"']


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE LA BIBLIOTECA PROPIA DE DATOS")
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
