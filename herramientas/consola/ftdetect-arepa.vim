" Detección de *.arepa para Vim (consola, sin plugins).
" Instalación en Linux (una sola vez):
"   mkdir -p ~/.vim/ftdetect
"   cp herramientas/consola/ftdetect-arepa.vim ~/.vim/ftdetect/arepa.vim
augroup arepa
  autocmd!
  autocmd BufNewFile,BufRead *.arepa set filetype=arepa
augroup END
