"""
AREPA - Pruebas de las estructuras propias (Corte A4)
-----------------------------------------------------
Ejecuta programas completos del DSL con el runtime propio y verifica
las estructuras en memoria y sus operaciones:

  * Lista: literales, vacía, anidada, acceso 1-based y errores;
  * Registro: literales con claves ID y de cadena, orden de claves y
    acceso anidado;
  * Tabla: 'arme' con y sin filas, columnas reservadas y 'desde_filas';
  * asignación indexada, 'agregue', 'saque' y 'recorra';
  * agregaciones en memoria (sume, promedie, mediana, minimo, maximo,
    desviacion, cuente) y funciones largo/columna/columnas;
  * regresiones: 'resuma', 'cuenteme t |> escoja [a]' y las potencias.

Ninguna prueba usa pandas ni bibliotecas de datos: todo corre sobre la
biblioteca propia (src/datos) y el runtime propio (src/runtime).

Uso:
    python3 pruebas/test_estructuras.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "generado"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datos.lista import Lista  # noqa: E402
from datos.registro import Registro  # noqa: E402
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
    """Ejecuta un programa que debe fallar; devuelve el error propio."""
    _, arbol, errores = analizar(programa)
    assert not errores, "el programa debería fallar en ejecución, no en parseo"
    try:
        EjecutorArepa().ejecutar(arbol)
    except ErrorArepa as problema:
        return problema
    raise AssertionError("el programa debería haber fallado: " + programa)


# ---------------------------------------------------------------------- #
# Lista
# ---------------------------------------------------------------------- #

@caso
def lista_literal_y_acceso_uno_based():
    ejecutor = correr("quihubo\nl = [10, 20, 30]\nx = l[1]\nz = l[3]\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("x") == 10
    assert ejecutor.contexto.simbolos.buscar("z") == 30


@caso
def lista_vacia_tiene_largo_cero():
    ejecutor = correr("quihubo\nl = []\nn = largo(l)\nchao\n")
    lista = ejecutor.contexto.simbolos.buscar("l")
    assert isinstance(lista, Lista)
    assert lista.largo() == 0
    assert ejecutor.contexto.simbolos.buscar("n") == 0


@caso
def lista_anidada_acceso_encadenado():
    ejecutor = correr(
        "quihubo\nm = [[1, 2], [3, 4]]\nx = m[2][1]\nz = m[1][2]\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("x") == 3
    assert ejecutor.contexto.simbolos.buscar("z") == 2


@caso
def acceso_directo_sobre_lista_literal():
    ejecutor = correr("quihubo\nx = [1, 2][1]\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("x") == 1


@caso
def lista_indice_fuera_de_rango():
    problema = correr_y_fallar("quihubo\nl = [1, 2]\nx = l[3]\nchao\n")
    assert "La lista tiene 2 elementos" in problema.mensaje
    assert "no existe el 3" in problema.mensaje
    assert "se cuenta desde 1" in problema.mensaje


@caso
def lista_indice_de_texto_rechazado():
    problema = correr_y_fallar('quihubo\nl = [1, 2]\nx = l["a"]\nchao\n')
    assert "índice para la lista debe ser un número entero" in problema.mensaje
    assert "texto" in problema.mensaje


# ---------------------------------------------------------------------- #
# Registro
# ---------------------------------------------------------------------- #

@caso
def registro_literal_con_claves_id():
    ejecutor = correr(
        'quihubo\nr = {nombre: "Ana", edad: 20}\n'
        'n = r["nombre"]\ne = r["edad"]\nchao\n'
    )
    registro = ejecutor.contexto.simbolos.buscar("r")
    assert isinstance(registro, Registro)
    assert registro.largo() == 2
    assert ejecutor.contexto.simbolos.buscar("n") == "Ana"
    assert ejecutor.contexto.simbolos.buscar("e") == 20


@caso
def registro_con_claves_de_cadena():
    ejecutor = correr(
        'quihubo\nr = {"nombre completo": "Ana", "edad": 20}\n'
        'x = r["nombre completo"]\nchao\n'
    )
    assert ejecutor.contexto.simbolos.buscar("x") == "Ana"


@caso
def registro_conserva_orden_de_claves():
    ejecutor = correr("quihubo\nr = {b: 2, a: 1, c: 3}\nchao\n")
    registro = ejecutor.contexto.simbolos.buscar("r")
    assert registro.claves() == ["b", "a", "c"]
    assert registro.valores() == [2, 1, 3]


@caso
def registro_clave_inexistente():
    problema = correr_y_fallar(
        'quihubo\nr = {nombre: "Ana"}\nx = r["edad"]\nchao\n'
    )
    assert "La clave 'edad' no existe" in problema.mensaje
    assert "nombre" in problema.mensaje


@caso
def registro_anidado():
    ejecutor = correr(
        'quihubo\nr = {persona: {nombre: "Ana", edad: 20}}\n'
        'x = r["persona"]["nombre"]\nchao\n'
    )
    assert ejecutor.contexto.simbolos.buscar("x") == "Ana"


# ---------------------------------------------------------------------- #
# Tabla en memoria ('arme')
# ---------------------------------------------------------------------- #

@caso
def arme_con_filas():
    ejecutor = correr(
        'quihubo\ngente = arme [nombre, edad] con [["Ana", 20], ["Luis", 31]]\n'
        'a = gente[1]["nombre"]\nb = gente[2]["edad"]\nchao\n'
    )
    tabla = ejecutor.contexto.simbolos.buscar("gente")
    assert isinstance(tabla, Tabla)
    assert tabla.nombres_columnas == ["nombre", "edad"]
    assert tabla.num_filas == 2
    assert ejecutor.contexto.simbolos.buscar("a") == "Ana"
    assert ejecutor.contexto.simbolos.buscar("b") == 31


@caso
def arme_sin_filas():
    ejecutor = correr("quihubo\nvacia = arme [nombre, edad]\nn = largo(vacia)\nchao\n")
    tabla = ejecutor.contexto.simbolos.buscar("vacia")
    assert tabla.nombres_columnas == ["nombre", "edad"]
    assert tabla.num_filas == 0
    assert ejecutor.contexto.simbolos.buscar("n") == 0


@caso
def arme_fila_con_largo_incorrecto():
    problema = correr_y_fallar(
        'quihubo\ng = arme [nombre, edad] con [["Ana"], ["Luis", 31]]\nchao\n'
    )
    assert "La fila 1 de 'arme' trae 1 valor" in problema.mensaje
    assert "2 columnas" in problema.mensaje


@caso
def arme_columnas_con_nombre_reservado():
    ejecutor = correr(
        'quihubo\ng = arme [numero, texto] con [[1, "uno"], [2, "dos"]]\n'
        'x = g[2]["texto"]\nchao\n'
    )
    assert ejecutor.contexto.simbolos.buscar("g").nombres_columnas == [
        "numero", "texto"
    ]
    assert ejecutor.contexto.simbolos.buscar("x") == "dos"


@caso
def tabla_desde_filas_directa():
    tabla = Tabla.desde_filas(
        ["nombre", "edad"], [["Ana", 20], ["Luis", 31]], nombre="gente"
    )
    assert tabla.nombres_columnas == ["nombre", "edad"]
    assert tabla.num_filas == 2
    assert tabla.filas[1].valores == ["Luis", 31]
    # Una fila con otro largo también se rechaza por la vía directa.
    try:
        Tabla.desde_filas(["nombre", "edad"], [["Ana"]], nombre="gente")
    except ErrorArepa as problema:
        assert "trae 1 valor" in problema.mensaje
    else:
        raise AssertionError("Tabla.desde_filas debería rechazar la fila corta")


# ---------------------------------------------------------------------- #
# Asignación indexada
# ---------------------------------------------------------------------- #

@caso
def asignacion_a_lista():
    ejecutor = correr("quihubo\nl = [1, 2, 3]\nl[2] = 9\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("l") == Lista([1, 9, 3])


@caso
def asignacion_a_registro():
    ejecutor = correr(
        'quihubo\nr = {nombre: "Ana", edad: 20}\nr["edad"] = 21\nchao\n'
    )
    assert ejecutor.contexto.simbolos.buscar("r").obtener("edad") == 21


@caso
def asignacion_a_celda_de_tabla():
    ejecutor = correr(
        'quihubo\ngente = arme [nombre, edad] con [["Ana", 20], ["Luis", 31]]\n'
        'gente[1]["edad"] = 21\nchao\n'
    )
    tabla = ejecutor.contexto.simbolos.buscar("gente")
    assert tabla.filas[0].valor_en(1) == 21
    assert tabla.filas[1].valor_en(1) == 31


@caso
def asignacion_a_fila_completa_con_lista():
    ejecutor = correr(
        'quihubo\ngente = arme [nombre, edad] con [["Ana", 20]]\n'
        'gente[1] = ["Beatriz", 22]\nchao\n'
    )
    fila = ejecutor.contexto.simbolos.buscar("gente").filas[0]
    assert fila.valores == ["Beatriz", 22]


@caso
def asignacion_a_fila_completa_con_registro():
    ejecutor = correr(
        'quihubo\ngente = arme [nombre, edad] con [["Ana", 20]]\n'
        'gente[1] = {nombre: "Beatriz", edad: 22}\nchao\n'
    )
    fila = ejecutor.contexto.simbolos.buscar("gente").filas[0]
    assert fila.valores == ["Beatriz", 22]


@caso
def asignacion_indexada_variable_inexistente():
    problema = correr_y_fallar("quihubo\nz[1] = 5\nchao\n")
    assert "La variable 'z' no esta declarada" in problema.mensaje
    assert "asignar dentro de ella" in problema.mensaje


# ---------------------------------------------------------------------- #
# 'agregue'
# ---------------------------------------------------------------------- #

@caso
def agregue_a_lista():
    ejecutor = correr("quihubo\nl = [1, 2]\nagregue 3 en l\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("l") == Lista([1, 2, 3])


@caso
def agregue_a_tabla_con_lista():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, edad] con [["Ana", 20]]\n'
        'agregue ["Luis", 31] en g\nchao\n'
    )
    tabla = ejecutor.contexto.simbolos.buscar("g")
    assert tabla.num_filas == 2
    assert tabla.filas[1].valores == ["Luis", 31]


@caso
def agregue_a_tabla_con_registro():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, edad] con [["Ana", 20]]\n'
        'agregue {nombre: "Luis", edad: 31} en g\nchao\n'
    )
    tabla = ejecutor.contexto.simbolos.buscar("g")
    assert tabla.num_filas == 2
    assert tabla.filas[1].valores == ["Luis", 31]


@caso
def agregue_a_destino_no_coleccion():
    problema = correr_y_fallar("quihubo\nx = 5\nagregue 1 en x\nchao\n")
    assert "solo trabaja sobre una tabla o una lista" in problema.mensaje
    assert "numero" in problema.mensaje


@caso
def agregue_fila_con_largo_incorrecto():
    problema = correr_y_fallar(
        'quihubo\ng = arme [nombre, edad] con [["Ana", 20]]\n'
        'agregue ["Luis"] en g\nchao\n'
    )
    assert "La fila trae 1 valor" in problema.mensaje
    assert "2 columnas" in problema.mensaje


# ---------------------------------------------------------------------- #
# 'saque'
# ---------------------------------------------------------------------- #

@caso
def saque_de_lista():
    ejecutor = correr("quihubo\nl = [1, 2, 3]\nsaque 2 de l\nchao\n")
    assert ejecutor.contexto.simbolos.buscar("l") == Lista([1, 3])


@caso
def saque_de_tabla():
    ejecutor = correr(
        'quihubo\ng = arme [nombre] con [["Ana"], ["Luis"]]\n'
        "saque 1 de g\nchao\n"
    )
    tabla = ejecutor.contexto.simbolos.buscar("g")
    assert tabla.num_filas == 1
    assert tabla.filas[0].valor_en(0) == "Luis"


@caso
def saque_posicion_invalida():
    fuera = correr_y_fallar("quihubo\nl = [1]\nsaque 2 de l\nchao\n")
    assert "tiene 1 elementos" in fuera.mensaje
    assert "no existe el 2" in fuera.mensaje

    no_entero = correr_y_fallar('quihubo\nl = [1]\nsaque "uno" de l\nchao\n')
    assert "necesita un numero entero" in no_entero.mensaje
    assert "texto" in no_entero.mensaje


# ---------------------------------------------------------------------- #
# 'recorra'
# ---------------------------------------------------------------------- #

@caso
def recorra_lista_acumula():
    ejecutor = correr(
        "quihubo\nl = [1, 2, 3]\ns = 0\nrecorra elem en l {\n"
        " s = s + elem\n}\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("s") == 6


@caso
def recorra_tabla_lee_columnas():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, edad] con [["Ana", 20], ["Luis", 31]]\n'
        's = 0\nrecorra fila en g {\n s = s + fila["edad"]\n}\nchao\n'
    )
    assert ejecutor.contexto.simbolos.buscar("s") == 51


@caso
def recorra_tabla_muta_celdas():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, edad] con [["Ana", 20], ["Luis", 31]]\n'
        'recorra fila en g {\n fila["edad"] = fila["edad"] + 1\n}\nchao\n'
    )
    tabla = ejecutor.contexto.simbolos.buscar("g")
    assert [f.valor_en(1) for f in tabla.filas] == [21, 32]


@caso
def recorra_con_pare():
    ejecutor = correr(
        "quihubo\nl = [1, 2, 3, 4]\ns = 0\nrecorra elem en l {\n"
        " s = s + elem\n fijese_si (elem == 2) {\n  pare\n }\n}\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("s") == 3


@caso
def recorra_con_siga():
    ejecutor = correr(
        "quihubo\nl = [1, 2, 3, 4]\ns = 0\nrecorra elem en l {\n"
        " fijese_si (elem == 2) {\n  siga\n }\n s = s + elem\n}\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("s") == 8


@caso
def recorra_sobre_numero_rechazado():
    problema = correr_y_fallar(
        "quihubo\nn = 5\nrecorra elem en n {\n}\nchao\n"
    )
    assert "necesita una tabla o una lista" in problema.mensaje
    assert "numero" in problema.mensaje


# ---------------------------------------------------------------------- #
# Agregaciones en memoria y funciones de estructura
# ---------------------------------------------------------------------- #

@caso
def agregaciones_de_tabla():
    ejecutor = correr(
        'quihubo\ng = arme [n] con [[10], [20], [30]]\n'
        "s = sume(g, n)\np = promedie(g, n)\n"
        "mn = minimo(g, n)\nmx = maximo(g, n)\nchao\n"
    )
    valores = ejecutor.contexto.simbolos
    assert valores.buscar("s") == 60
    assert valores.buscar("p") == 20.0
    assert valores.buscar("mn") == 10
    assert valores.buscar("mx") == 30


@caso
def mediana_par_e_impar():
    ejecutor = correr(
        "quihubo\nimpar = arme [n] con [[10], [20], [30]]\n"
        "par = arme [n] con [[10], [20], [30], [40]]\n"
        "mi = mediana(impar, n)\nmp = mediana(par, n)\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("mi") == 20
    assert ejecutor.contexto.simbolos.buscar("mp") == 25.0


@caso
def desviacion_poblacional():
    ejecutor = correr(
        "quihubo\ng = arme [n] con [[10], [20], [30]]\nd = desviacion(g, n)\nchao\n"
    )
    esperada = (200.0 / 3.0) ** 0.5
    assert abs(ejecutor.contexto.simbolos.buscar("d") - esperada) < 1e-9


@caso
def cuente_tabla_y_columna_con_nada():
    ejecutor = correr(
        "quihubo\ng = arme [n] con [[1], [nada], [3]]\n"
        "todas = cuente(g)\npresentes = cuente(g, n)\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("todas") == 3
    assert ejecutor.contexto.simbolos.buscar("presentes") == 2


@caso
def agregaciones_de_lista():
    ejecutor = correr(
        "quihubo\nl = [1, 2, 3.5]\ns = sume(l)\nc = cuente(l)\nchao\n"
    )
    assert ejecutor.contexto.simbolos.buscar("s") == 6.5
    assert ejecutor.contexto.simbolos.buscar("c") == 3


@caso
def columna_devuelve_lista():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, n] con [["a", 10], ["b", 20]]\n'
        "c = columna(g, n)\nchao\n"
    )
    columna = ejecutor.contexto.simbolos.buscar("c")
    assert isinstance(columna, Lista)
    assert columna.obtener(0) == 10
    assert columna.obtener(1) == 20


@caso
def columnas_devuelve_nombres():
    ejecutor = correr(
        'quihubo\ng = arme [nombre, n] con [["a", 10]]\nc = columnas(g)\nchao\n'
    )
    columnas = ejecutor.contexto.simbolos.buscar("c")
    assert isinstance(columnas, Lista)
    assert columnas.obtener(0) == "nombre"
    assert columnas.obtener(1) == "n"


@caso
def largo_de_tabla_lista_registro_y_texto():
    ejecutor = correr(
        "quihubo\nl = [1, 2]\ng = arme [a] con [[1], [2], [3]]\n"
        'r = {x: 1, y: 2}\na = largo(l)\nb = largo(g)\n'
        'c = largo(r)\nd = largo("hola")\nchao\n'
    )
    simbolos = ejecutor.contexto.simbolos
    assert (simbolos.buscar("a"), simbolos.buscar("b")) == (2, 3)
    assert (simbolos.buscar("c"), simbolos.buscar("d")) == (2, 4)


# ---------------------------------------------------------------------- #
# Regresiones de A1/A2/A3
# ---------------------------------------------------------------------- #

@caso
def resuma_sigue_funcionando():
    ejecutor = correr(
        'quihubo\ng = arme [ciudad, n] con [["Bogota", 10], '
        '["Cali", 20], ["Bogota", 5]]\n'
        "r = g |> junte por [ciudad] |> resuma total = sume(n), regs = cuente()\n"
        "chao\n"
    )
    resumen = ejecutor.contexto.simbolos.buscar("r")
    assert resumen.nombres_columnas == ["ciudad", "total", "regs"]
    por_ciudad = dict(
        (f.valor_en(0), (f.valor_en(1), f.valor_en(2))) for f in resumen.filas
    )
    assert por_ciudad["Bogota"] == (15, 2)
    assert por_ciudad["Cali"] == (20, 1)


@caso
def cuenteme_pipeline_imprime_la_tabla():
    ejecutor = correr(
        "quihubo\ng = arme [a, b] con [[1, 2], [3, 4]]\n"
        "cuenteme g |> escoja [a]\nchao\n"
    )
    assert len(ejecutor.contexto.salida) == 1
    linea = ejecutor.contexto.salida[0]
    assert "None" not in linea
    assert linea.strip().splitlines()[0] == "a"
    assert "1" in linea and "3" in linea


@caso
def potencias_precedencia_y_signo():
    ejecutor = correr(
        "quihubo\na = -2 ^ 2\nb = 2 ^ 3 ^ 2\nc = 2 ^ -3\nchao\n"
    )
    simbolos = ejecutor.contexto.simbolos
    assert simbolos.buscar("a") == -4
    assert simbolos.buscar("b") == 512
    assert simbolos.buscar("c") == 0.125


@caso
def acceso_a_tabla_fuera_de_rango_menciona_filas():
    problema = correr_y_fallar(
        'quihubo\ngente = arme [nombre] con [["Ana"], ["Luis"]]\n'
        "x = gente[3]\nchao\n"
    )
    assert "tiene 2 filas" in problema.mensaje
    assert "no existe la 3" in problema.mensaje
    assert "se cuenta desde 1" in problema.mensaje


def main():
    pasaron = fallaron = 0
    print("=" * 78)
    print(" PRUEBAS DE ESTRUCTURAS PROPIAS (LISTAS, REGISTROS Y TABLAS)")
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
