@echo off
REM ============================================================
REM  AREPA - Regenera el lexer y el parser desde la gramatica
REM  Requiere: Java 11+ y antlr-4.13.2-complete.jar
REM  Si tiene antlr4-tools instalado (pip install antlr4-tools),
REM  puede ejecutar directamente:
REM     antlr4 -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
REM ============================================================
setlocal
set JAR=%ANTLR_JAR%
if "%JAR%"=="" set JAR=%USERPROFILE%\antlr\antlr-4.13.2-complete.jar

if not exist "%JAR%" (
    echo No encontre el jar de ANTLR en "%JAR%".
    echo Descarguelo de https://www.antlr.org/download.html o defina ANTLR_JAR.
    exit /b 1
)

set JAVA=java
if exist "%USERPROFILE%\.jdk\jdk-17.0.20.1+1\bin\java.exe" set JAVA=%USERPROFILE%\.jdk\jdk-17.0.20.1+1\bin\java.exe

"%JAVA%" -jar "%JAR%" -Dlanguage=Python3 -visitor -no-listener -o generado gramatica/Arepa.g4
if %errorlevel%==0 (
    echo Listo: codigo generado en generado\
) else (
    echo Paila: la generacion fallo.
    exit /b 1
)
endlocal
