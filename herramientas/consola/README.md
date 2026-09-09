# Autocompletado de AREPA en consola (Linux, sin internet ni plugins)

Tres herramientas, todas con `Tab`. Palabras tomadas de `gramatica/Arepa.g4`
(51 reservadas + `|>` `->` `==` `!=` `<=` `>=`).

| Archivo | Qué es |
|---|---|
| `arepa.vim` | plugin de Vim: fantasma gris + `Tab`, resalta y trae `:ArepaPlantilla` |
| `ftdetect-arepa.vim` | detecta `*.arepa` en Vim |
| `palabras_arepa.txt` | diccionario (respaldo del plugin) |
| `arepa` | lanzador del CLI (`arepa programa.arepa --ejecutar`) |
| `arepa_bash.sh` | `Tab` en Bash: completa `.arepa` y `--arbol/--tokens/--ejecutar` |
| `practica.arepa` | hoja de 9 ejercicios de `Tab` (válida: también corre) |
| REPL | `python3 src/cli/repl.py`: consola AREPA con `Tab` |

## 1. Vim (editar `.arepa`)

```bash
mkdir -p ~/.vim/ftplugin ~/.vim/ftdetect
cp herramientas/consola/arepa.vim ~/.vim/ftplugin/arepa.vim
cp herramientas/consola/ftdetect-arepa.vim ~/.vim/ftdetect/arepa.vim
vim herramientas/consola/practica.arepa
```

Ejemplos (modo inserción):

* Escribes `mon` y al fondo aparece `te` en gris → `Tab` o `Ctrl-F` deja `monte`.
* Escribes `|` y aparece `>` en gris → `Tab` deja `|>`.
* Escribes `pa_` y aparece `abajo` en gris (`pa_abajo` es la primera opción).

| Escribes | Fantasma gris | Tab deja |
|---|---|---|
| `mon` | `te` | `monte` |
| `esc` | `oja` | `escoja` |
| `pa_` | `abajo` | `pa_abajo` |
| `\|` | `>` | `\|>` |
| `fij` | `ese_si` | `fijese_si` |
| `bar` | `ras` | `barras` |
| `guar` | `dela` | `guardela` |

Plantillas (modo normal):

```vim
:ArepaPlantilla <Tab>     " lista: base monte tuberia resumen pinte funcion fijese
:ArepaPlantilla tuberia   " inserta el bloque |> escoja/deje/cree
```

`Ctrl-N` / `Ctrl-P` completan además con palabras del archivo abierto.

## 2. REPL (fantasma mientras escribes AREPA)

```bash
python3 src/cli/repl.py            # con fantasma (Linux en terminal)
python3 src/cli/repl.py --simple   # modo clásico (readline o donde no hay tty)
```

```text
arepa> mon[te en gris]             # escribes "mon", el resto aparece solo
arepa> mon + Tab                   # acepta y deja "monte"
arepa> :plantilla monte            # inserta la línea de monte
arepa> :plantilla tuberia          # inserta el pipeline de ejemplo
arepa> :ver                        # muestra lo escrito
arepa> :validar                    # valida con el front-end ANTLR
¡Quihubo pues! Programa bien escrito.
arepa> :ejemplo demo               # carga ejemplos/demo.arepa (Tab completa el nombre)
arepa> :guardar salidas/<Tab>      # Tab completa archivos .arepa y carpetas
arepa> :salir
```

Teclas del modo fantasma: `Tab`/`FlechaDer` acepta, `Flechas` navegan e
historial (`Arriba`/`Abajo`), `Retroceso` borra, `Ctrl-U` limpia,
`Ctrl-C` cancela la línea, `Ctrl-D` sale.

Si una línea empieza con una palabra desconocida, sugiere parecidas:

```text
arepa> mont "x.csv"
  (¿quisiste decir: monte ? Tab para completar)
```

El historial queda en `~/.arepa_history`.

## 3. Bash (lanzador + opciones del CLI)

```bash
ln -s "$PWD/herramientas/consola/arepa" ~/.local/bin/arepa
source herramientas/consola/arepa_bash.sh   # o añádelo a ~/.bashrc
arepa <Tab>              # propone programas .arepa
arepa practica.arepa --<Tab>  # propone --arbol --tokens --ejecutar --help
```

## 4. Practicar

`practica.arepa` trae 9 ejercicios guiados (TAB 1–9). También valida:

```bash
arepa herramientas/consola/practica.arepa
arepa herramientas/consola/practica.arepa --ejecutar
```
