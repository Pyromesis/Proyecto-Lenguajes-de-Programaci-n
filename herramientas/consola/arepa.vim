" AREPA para Vim (100% consola, sin plugins ni internet).
" Instalación en Linux:
"   mkdir -p ~/.vim/ftdetect ~/.vim/syntax ~/.vim/ftplugin
"   cp herramientas/consola/arepa.vim ~/.vim/ftplugin/arepa.vim
"   echo 'au BufNewFile,BufRead *.arepa set filetype=arepa' >> ~/.vimrc
" Uso editando un .arepa en vim:
"   Ctrl-N / Ctrl-P : completar palabra del diccionario
"   Tab             : lo mismo (mapeado abajo)
"   |> , = , == ...: se completan como palabras del buffer

if exists("b:did_ftplugin_arepa")
  finish
endif
let b:did_ftplugin_arepa = 1

" Diccionario: está junto a este archivo.
let s:dict = expand('<sfile>:p:h') . '/palabras_arepa.txt'
if filereadable(s:dict)
  let &l:dictionary = s:dict
  setlocal complete+=k
endif

" El guion bajo y '|' '>' hacen parte de las palabras para pa_arriba e |>.
setlocal iskeyword+=_,|,>
setlocal tabstop=4 shiftwidth=4 expandtab
setlocal commentstring=#\ %s

" Resaltado mínimo de las reservadas (sin plugin externo).
if has("syntax")
  syntax keyword arepaEstructura quihubo chao
  syntax keyword arepaDatos monte guarde como con encabezado separador
  syntax keyword arepaTrans escoja deje donde acomode por pa_arriba pa_abajo
  syntax keyword arepaTrans cree renombre limpie duplicados vacios convierta junte resuma
  syntax keyword arepaTipos numero texto logico fecha
  syntax keyword arepaGraf pinte barras lineas histograma dispersion cajas titulo ejex ejey leyenda guardela muestrela
  syntax keyword arepaControl invente devuelva fijese_si sino cuenteme describa
  syntax keyword arepaBool obvio falso nada y o no
  highlight default link arepaEstructura Structure
  highlight default link arepaDatos Keyword
  highlight default link arepaTrans Function
  highlight default link arepaTipos Type
  highlight default link arepaGraf String
  highlight default link arepaControl Conditional
  highlight default link arepaBool Boolean
endif

" Tab completa como Ctrl-N cuando hay palabra antes del cursor.
inoremap <buffer><expr> <Tab> pumvisible() ? "\<C-n>" : (col('.') > 1 && getline('.')[col('.')-2] =~ '\k' ? "\<C-n>" : "\<Tab>")
