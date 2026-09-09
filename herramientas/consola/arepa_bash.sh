# Autocompletado Bash para el lanzador `arepa` (consola, Linux).
# Completa archivos .arepa y las opciones del CLI (--arbol/--tokens/--ejecutar).
# Instalación (una sola vez):
#   source "$PWD/herramientas/consola/arepa_bash.sh"
#   # o para siempre:
#   echo 'source "$HOME/Proyecto/herramientas/consola/arepa_bash.sh"' >> ~/.bashrc
# Uso:
#   arepa <Tab>          -> lista programas .arepa y directorios
#   arepa prog.arepa --<Tab> -> --arbol --tokens --ejecutar --help

_arepa() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "--arbol --tokens --ejecutar --help" -- "$cur"))
        return 0
    fi
    COMPREPLY=()
    local f
    for f in $(compgen -f -- "$cur"); do
        if [[ -d "$f" ]]; then
            COMPREPLY+=("$f/")
        elif [[ "$f" == *.arepa ]]; then
            COMPREPLY+=("$f")
        fi
    done
}
complete -F _arepa arepa
