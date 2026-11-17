"""Ayudas de consola: una causa concreta y una acción para corregirla.

No decide qué es válido: esa responsabilidad sigue en el lexer, parser y
runtime. Tampoco convierte los avisos aritméticos en errores.
"""
from utiles.texto import quitar_tildes


def ayuda_error(problema):
    mensaje = quitar_tildes(problema.mensaje).lower()
    clase = type(problema).__name__
    if "interno" in mensaje:
        return "Conservá el programa y el diagnóstico para revisar el intérprete; este fallo no confirma que tu código AREPA esté mal."
    if clase == "ErrorCSV":
        if "repetidos" in mensaje:
            return "Dale un nombre único a cada columna del encabezado, incluidos los nombres automáticos columna_1, columna_2, etc."
        if "comillas" in mensaje:
            return 'Cerrá cada campo entre comillas dobles; para incluir una comilla dentro, escribila dos veces: "".'
        if "vacio" in mensaje:
            return "Agregá un encabezado o datos al CSV; una tabla sin filas puede tener solo su encabezado."
        if "separador" in mensaje:
            return 'Indicá un solo carácter, por ejemplo: monte "datos.csv" con encabezado, separador ";".'
        return "Comprobá el separador y que cada fila respete las columnas del encabezado; entrecomillá los campos que contienen separadores."
    if clase == "ErrorArchivo":
        if "utf-8" in mensaje or "codific" in mensaje:
            return "Guardá el archivo como texto UTF-8 y volvé a ejecutarlo."
        if "guardar" in mensaje or "escribir" in mensaje:
            return "Usá una ruta de archivo válida, comprobá que el destino no sea una carpeta y que tengas permiso para escribir allí."
        return "Revisá que el archivo exista, que la ruta sea válida y que tengas permiso para leerlo; las rutas relativas parten de la carpeta actual de la terminal."
    if clase == "ErrorVariable":
        if "funcion" in mensaje:
            return "Definí la función con invente antes de llamarla y comprobá su nombre."
        if "modelo" in mensaje:
            return "Creá el modelo con entrene antes de usar prediga, clasifique o evalua."
        return "Asigná la variable antes de usarla y comprobá su nombre; para una tabla, usá monte o arme."
    if clase == "ErrorColumna":
        if "ya existe" in mensaje or "repetido" in mensaje:
            return "Usá un nombre nuevo para la columna calculada o el destino del renombre; no puede coincidir con otra columna existente."
        return "Usá uno de los nombres de columnas o claves disponibles; respetá tildes, mayúsculas y cualquier renombre realizado antes de esta instrucción."
    if "recurs" in mensaje or "pila" in mensaje:
        return "Agregá un caso base alcanzable y hacé que cada llamada se acerque a él; reducí la profundidad de la entrada si es necesario."
    if "diverg" in mensaje or "no finito" in mensaje or "no finita" in mensaje or "rango decimal" in mensaje:
        return "Usá números finitos, reducí la tasa de aprendizaje y revisá la escala de las columnas y del objetivo. Un entrenamiento inválido no puede evaluarse como exitoso."
    if "vueltas" in mensaje or "iteracion" in mensaje:
        return "Comprobá que la condición del ciclo pueda volverse falso y que el cuerpo actualice la variable de control."
    if "parametros repetidos" in mensaje:
        return "Dale un nombre distinto a cada parámetro de la función; no lo declares dos veces en la misma definición."
    if "parametro" in mensaje or "argumento" in mensaje:
        return "Compará la llamada con la definición: pasá la cantidad de argumentos indicada, en el mismo orden y con los tipos esperados."
    if any(p in mensaje for p in ("'pare'", "'siga'")):
        return "Colocá pare o siga dentro de repita, mientras o recorra; solo controlan un ciclo activo."
    if "'devuelva'" in mensaje:
        return "Colocá devuelva dentro del bloque de una función definida con invente."
    if "paso" in mensaje:
        return "Usá un paso entero distinto de cero y coherente con el sentido del rango."
    if "veces" in mensaje or "cantidad de repeticiones" in mensaje:
        return "Usá una cantidad entera mayor o igual que cero; repita 0 veces es válido."
    if "fecha" in mensaje:
        return "Usá una fecha real con formato AAAA-MM-DD; verificá días del mes y si febrero tiene 28 o 29 días."
    if "desde 1" in mensaje or "indice" in mensaje:
        return "Los índices de listas y filas son enteros desde 1 hasta su tamaño; no se puede indexar una colección vacía. En registros, usá una clave de texto."
    if "fila" in mensaje and ("columnas" in mensaje or "valores" in mensaje):
        return "Dale a cada fila un valor por columna; si usás un registro, incluí las claves requeridas por la tabla."
    if "condicion" in mensaje:
        return "Usá una comparación que produzca obvio o falso; en fijese_si y mientras, nada y los números no son condiciones lógicas."
    if clase == "ErrorGrafica":
        if "no tiene filas" in mensaje or "vacia" in mensaje:
            return "Revisá los filtros anteriores y proporcioná al menos una fila para graficar; una tabla vacía sí puede guardarse en CSV o resumirse."
        if ".png" in mensaje:
            return 'Guardá la imagen con extensión .png, por ejemplo: guardela "salidas/grafica.png".'
        if "histograma" in mensaje:
            return "Elegí exactamente una columna numérica en ejey para el histograma."
        if "repet" in mensaje or "mas de una" in mensaje or "ya " in mensaje:
            return "Dejá una sola cláusula de cada tipo; para varias series, usá ejey [columna1, columna2]."
        if "escribir" in mensaje or "guardar" in mensaje:
            return "Comprobá la ruta de salida, sus permisos y que el destino sea un archivo PNG."
        return "Revisá que ejex y ejey existan, que las series de ejey sean numéricas y que no se repitan las cláusulas de la gráfica."
    if "no tiene resultado real" in mensaje:
        return "Usá una base no negativa para exponentes fraccionarios o un exponente entero; AREPA no representa números complejos."
    if "rango numerico" in mensaje or "magnitud" in mensaje:
        return "Reducí la magnitud de los valores o cambiá la escala para mantener el cálculo dentro del rango admitido."
    if "convertir" in mensaje:
        return "Limpiá el valor antes de convertirlo: numero admite texto numérico, logico admite obvio/falso y fecha exige AAAA-MM-DD."
    if "no es una tabla" in mensaje or "necesita una tabla" in mensaje or "tabla de entrada" in mensaje:
        return "Creá o cargá una tabla con arme o monte; las etapas de datos se encadenan así: tabla |> operación."
    if "clave" in mensaje and "texto" in mensaje:
        return 'Accedé al registro mediante una clave de texto, por ejemplo: persona["nombre"].'
    if "tasa" in mensaje or "epocas" in mensaje:
        return "Usá tasa positiva y finita y epocas como entero positivo; tasa/epocas corresponden a regresión y perceptrón, no al árbol."
    if "profundidad" in mensaje or "min_hojas" in mensaje:
        return "Usá profundidad y min_hojas como enteros positivos solo en modelos arbol; para regresión o perceptrón corresponden tasa y epocas."
    if "clases" in mensaje or "binario" in mensaje:
        if "regresion" in mensaje:
            return "Quitá la opción clases de la regresión; su objetivo debe ser numérico. Para etiquetas usá perceptron o arbol."
        return "Comprobá las clases de entrenamiento: el perceptrón exige dos clases; para más clases usá un árbol y una lista coherente."
    if "objetivo" in mensaje or "entren" in mensaje or "modelo" in mensaje:
        return "Revisá columnas y objetivo, eliminá objetivos vacíos y entrená el modelo adecuado antes de evaluar; prediga usa regresión y clasifique usa clasificación."
    if clase == "ErrorTipos":
        return "Usá operandos compatibles: aritmética con números, lógica con obvio/falso y comparaciones entre tipos compatibles; convertí explícitamente si corresponde."
    if clase == "ErrorOperacion":
        return "Revisá los valores y la estructura que recibe esta operación; el mensaje indica la restricción que no se cumple."
    return "Revisá la instrucción señalada y sus datos de entrada; corregí la causa indicada antes de volver a ejecutar."


def ayuda_sintaxis(error):
    mensaje = error["mensaje"]
    detalle = error.get("detalle", "")
    if error["tipo"] == "léxico":
        if '\'"' in detalle:
            return 'Cerrá la cadena con comillas dobles; los saltos dentro del texto se escriben como \\n y las comillas internas como \\".'
        return "Retirá o reemplazá el símbolo señalado; usá los operadores y las palabras del lenguaje AREPA."
    if "reservada" in mensaje:
        return "Elegí otro nombre para la variable; las palabras reservadas siguen siendo válidas como nombres de columna."
    return "Revisá el elemento esperado y los delimitadores de la instrucción; separá las sentencias con saltos de línea y cerrá el programa con chao."
