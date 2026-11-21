@echo off
chcp 65001 >nul
title ATALAIA 4.0 — Resetar Usuarios

echo.
echo ============================================================
echo         ATALAIA 4.0 — Resetar Usuarios de Teste
echo ============================================================
echo.
echo Este script apaga e recria os tres usuarios de teste.
echo As senhas serao lidas do arquivo .env.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo        Execute iniciar.bat primeiro para configurar o projeto.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado.
    echo        Execute iniciar.bat primeiro para configurar o projeto.
    pause
    exit /b 1
)

.venv\Scripts\python.exe criar_usuarios_teste.py --resetar
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao resetar usuarios.
    echo        Verifique se o MySQL esta ligado no XAMPP.
    pause
    exit /b 1
)

echo Pronto. Execute iniciar.bat para iniciar o sistema.
pause
