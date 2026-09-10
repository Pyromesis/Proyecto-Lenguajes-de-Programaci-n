" AREPA para Vim (100% consola, sin plugins ni internet).
" Instalación en Linux (una sola vez):
"   mkdir -p ~/.vim/ftplugin ~/.vim/ftdetect
"   cp herramientas/consola/arepa.vim ~/.vim/ftplugin/arepa.vim
"   cp herramientas/consola/ftdetect-arepa.vim ~/.vim/ftdetect/arepa.vim
" Uso editando un .arepa en vim:
"   Fantasma gris  : muestra lo que Tab completaría; Tab o Ctrl-F lo acepta
"   Tab             : acepta el fantasma, si no completa palabras de AREPA
"   Ctrl-N / Ctrl-P : completar con palabras del archivo abierto
"   |> , -> , == ..: también se completan con Tab
"   :ArepaPlantilla : inserta un esqueleto (base, monte, tuberia, ...)

if exists("b:did_ftplugin_arepa")
  finish
endif
let b:did_ftplugin_arepa = 1

" Lista autocontenida (misma que palabras_arepa.txt, de gramatica/Arepa.g4).
let s:palabras = ['quihubo', 'chao', 'monte', 'guarde', 'como', 'con',
      \ 'encabezado', 'separador', 'escoja', 'deje', 'donde', 'acomode',
      \ 'por', 'pa_arriba', 'pa_abajo', 'cree', 'renombre', 'limpie',
      \ 'duplicados', 'vacios', 'convierta', 'junte', 'resuma', 'numero',
      \ 'texto', 'logico', 'fecha', 'pinte', 'barras', 'lineas',
      \ 'histograma', 'dispersion', 'cajas', 'titulo', 'ejex', 'ejey',
      \ 'leyenda', 'guardela', 'muestrela', 'invente', 'devuelva',
      \ 'fijese_si', 'sino', 'cuenteme', 'describa', 'mientras', 'repita',
      \ 'veces', 'desde', 'hasta', 'paso', 'pare', 'siga', 'obvio', 'falso',
      \ 'nada', 'y', 'o', 'no', '|>', '->', '==', '!=', '<=', '>=']

" Si el diccionario está junto a este archivo, también se usa (Ctrl-N).
let s:dict = expand('<sfile>:p:h') . '/palabras_arepa.txt'
if filereadable(s:dict)
  let &l:dictionary = s:dict
endif
setlocal complete+=k,w,b

" Función de completado propia: filtra s:palabras por el prefijo.
function! ArepaComplete(findstart, base) abort
  if a:findstart
    let l:line = getline('.')
    let l:start = col('.') - 1
    while l:start > 0 && l:line[l:start - 1] =~ '\k\|[{|>]'
      let l:start -= 1
    endwhile
    return l:start
  else
    return filter(copy(s:palabras), 'v:val =~ "^" . escape(a:base, "[]{}.*^$\\~")')
  endif
endfunction
setlocal completefunc=ArepaComplete

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
  syntax keyword arepaControl invente devuelva fijese_si sino cuenteme describa mientras repita veces desde hasta paso pare siga
  syntax keyword arepaBool obvio falso nada y o no
  highlight default link arepaEstructura Structure
  highlight default link arepaDatos Keyword
  highlight default link arepaTrans Function
  highlight default link arepaTipos Type
  highlight default link arepaGraf String
  highlight default link arepaControl Conditional
  highlight default link arepaBool Boolean
endif

" Tab: acepta el fantasma; si no, menú; si no, completa AREPA; si no, Tab.
function! s:TabArepa() abort
  if pumvisible()
    return "\<C-n>"
  endif
  let l:aceptado = <SID>AceptarFantasma()
  if !empty(l:aceptado)
    return l:aceptado
  endif
  let l:c = col('.')
  if l:c > 1 && getline('.')[l:c - 2] =~ '\k\|[|>]'
    return "\<C-x>\<C-u>"
  endif
  return "\<Tab>"
endfunction
inoremap <buffer><expr> <Tab> <SID>TabArepa()
inoremap <buffer><expr> <C-f> <SID>AceptarFantasma()

" Texto fantasma: pinta en gris (virtual text) lo que Tab completaría.
let s:fantasma = ''
let s:fantasma_ok = has('textprop') && exists('*prop_add')
if s:fantasma_ok
  highlight default ArepaGhost ctermfg=244 guifg=#8a8a8a
  silent! call prop_type_add('ArepaGhost', {'highlight': 'ArepaGhost'})
endif

function! s:Fantasma() abort
  let s:fantasma = ''
  if !s:fantasma_ok || mode() !=# 'i'
    return ''
  endif
  try
    call prop_remove({'type': 'ArepaGhost', 'all': v:true})
    let l:c = col('.')
    let l:ln = getline('.')
    let l:i = l:c - 1
    while l:i > 0 && l:ln[l:i - 1] =~ '\k\|[|>]'
      let l:i -= 1
    endwhile
    let l:frag = strpart(l:ln, l:i, l:c - 1 - l:i)
    if empty(l:frag)
      return ''
    endif
    let l:cands = filter(copy(s:palabras), 'v:val =~ "^" . escape(l:frag, "[]{}.*^$\\~")')
    if empty(l:cands) || l:cands[0] ==# l:frag
      return ''
    endif
    let s:fantasma = strpart(l:cands[0], strlen(l:frag))
    call prop_add(line('.'), col('$'), {'type': 'ArepaGhost', 'text': '  ' . s:fantasma})
  catch
    let s:fantasma_ok = v:false
  endtry
  return ''
endfunction

function! s:AceptarFantasma() abort
  if empty(s:fantasma)
    return ''
  endif
  let l:s = s:fantasma
  let s:fantasma = ''
  silent! call prop_remove({'type': 'ArepaGhost', 'all': v:true})
  return l:s
endfunction

function! s:LimpiarFantasma() abort
  let s:fantasma = ''
  silent! call prop_remove({'type': 'ArepaGhost', 'all': v:true})
  return ''
endfunction

if s:fantasma_ok
  augroup ArepaGhost
    autocmd! * <buffer>
    autocmd TextChangedI <buffer> call <SID>Fantasma()
    autocmd CursorMovedI <buffer> call <SID>Fantasma()
    autocmd InsertLeave <buffer> call <SID>LimpiarFantasma()
  augroup END
endif

" Esqueletos listos: :ArepaPlantilla monte (Tab también completa el nombre).
let g:arepa_plantillas = {
      \ 'base': ['quihubo', '', '', 'chao'],
      \ 'monte': ['datos = monte "datos/archivo.csv" con encabezado, separador ","'],
      \ 'tuberia': ['resultado = datos',
      \             '|> escoja [col1, col2]',
      \             '|> deje donde col1 > 0',
      \             '|> cree total = col1 * col2'],
      \ 'resumen': ['resumen = resultado',
      \             '|> junte por [col1]',
      \             '|> resuma total = sume(total), n = cuente()'],
      \ 'pinte': ['pinte barras resumen',
      \           'titulo "Titulo"',
      \           'ejex col1',
      \           'ejey total',
      \           'guardela "salidas/grafica.png"'],
      \ 'funcion': ['invente doble(x) {',
      \             '    devuelva x * 2',
      \             '}'],
      \ 'fijese': ['fijese_si (x > 0) {',
      \            '    cuenteme "positivo"',
      \            '} sino {',
      \            '    cuenteme "cero o menos"',
      \            '}'],
      \ 'ciclo': ['mientras (x > 0) {',
      \           '    x = x - 1',
      \           '}'],
      \ }

function! ArepaListaPlantillas(A, L, P) abort
  return filter(sort(keys(g:arepa_plantillas)), 'v:val =~ "^" . a:A')
endfunction

function! s:Plantilla(nombre) abort
  if !has_key(g:arepa_plantillas, a:nombre)
    echo 'Plantillas: ' . join(sort(keys(g:arepa_plantillas)), ', ')
    return
  endif
  call append(line('.'), g:arepa_plantillas[a:nombre])
  call cursor(line('.') + 1, 1)
endfunction
command! -buffer -nargs=? -complete=customlist,ArepaListaPlantillas ArepaPlantilla call <SID>Plantilla(<q-args>)
