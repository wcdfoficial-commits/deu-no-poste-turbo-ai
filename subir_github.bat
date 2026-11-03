@echo off
chcp 65001 >nul
title DEU NO POSTE TURBO AI - Enviar para o GitHub
color 0B

echo ================================================================
echo           SUBIR PROJETO PARA O GITHUB (RENDER DEPLOY)
echo ================================================================
echo.
cd /d "%~dp0"

echo O repositorio Git local ja esta 100%% preparado e comitado no branch main!
echo.
echo Quando voce criar o novo repositorio vazio no GitHub (ex: deu-no-poste-turbo-ai),
echo copie o link HTTPS dele (terminado em .git).
echo.
set /p REPO_URL="Cole aqui a URL do seu repositorio no GitHub e aperte ENTER: "

if "%REPO_URL%"=="" (
    echo [ERRO] Nenhuma URL informada. Operacao cancelada.
    pause
    exit /b 1
)

echo.
echo [1/3] Configurando o repositorio remoto...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [2/3] Enviando arquivos para o GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo  [SUCESSO] Repositorio enviado para o GitHub com sucesso!
    echo.
    echo  Proximo passo no Render (render.com):
    echo  1. Va em "New" ^> "Web Service".
    echo  2. Conecte este repositorio do GitHub.
    echo  3. O Render ja detectara o render.yaml e iniciara o deploy!
    echo ================================================================
) else (
    echo.
    echo [ERRO] Ocorreu uma falha no envio.
    echo Certifique-se de estar conectado com a nova conta no GitHub.
)

echo.
pause
