@echo off
title DEU NO POSTE TURBO AI - Servidor Local
color 0A

echo ================================================================
echo           DEU NO POSTE TURBO AI (PRO) - INICIALIZADOR
echo ================================================================
echo.
cd /d "%~dp0"

echo [1/3] Verificando ambiente de execucao...

set "UV_PATH=%USERPROFILE%\.local\bin\uv.exe"

if exist "%UV_PATH%" (
    echo [OK] Ambiente uv detectado com sucesso.
    goto INICIAR_UV
)

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] uv detectado no PATH do Windows.
    set "UV_PATH=uv"
    goto INICIAR_UV
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python detectado. Instalando/verificando dependencias...
    python -m pip install -r requirements.txt
    echo.
    echo [2/3] Agendando abertura do navegador em http://localhost:8000 ...
    start /b cmd /c "ping -n 5 127.0.0.1 >nul && start http://localhost:8000"
    echo [3/3] Iniciando servidor FastAPI local na porta 8000...
    echo Para encerrar o servidor, pressione CTRL + C.
    echo.
    python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
    goto FIM
)

echo [ERRO] Python ou uv nao foram encontrados!
echo Por favor, certifique-se de ter o Python ou uv instalado.
pause
exit /b 1

:INICIAR_UV
echo [2/3] Agendando abertura do navegador em http://localhost:8000 ...
start /b cmd /c "ping -n 5 127.0.0.1 >nul && start http://localhost:8000"

echo [3/3] Iniciando servidor com uv na porta 8000...
echo.
echo ================================================================
echo  Painel Web disponivel em: http://localhost:8000
echo  (Se abrir antes de carregar, basta dar F5 no navegador)
echo  Para fechar o servidor: feche esta janela ou aperte CTRL + C
echo ================================================================
echo.

"%UV_PATH%" run --with fastapi,uvicorn,requests,beautifulsoup4,pandas,pydantic python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

:FIM
pause
