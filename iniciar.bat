@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title ATALAIA 4.0

echo.
echo ============================================================
echo            ATALAIA 4.0 — Inicializando...
echo ============================================================
echo.

REM ---- 1. Verificar Python ----------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no sistema.
    echo        Baixe e instale em: https://www.python.org/downloads/
    echo        Na instalacao, marque "Add Python to PATH".
    pause
    exit /b 1
)
echo [1/6] Python encontrado.

REM ---- 2. Criar ambiente virtual ----------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [2/6] Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo       Ambiente virtual criado.
) else (
    echo [2/6] Ambiente virtual ja existe.
)

REM ---- 3. Instalar dependencias -----------------------------------
echo [3/6] Verificando dependencias...
.venv\Scripts\python.exe -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo       Instalando... ^(pode demorar alguns minutos na primeira vez^)
    .venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias.
        echo        Verifique sua conexao com a internet e tente novamente.
        pause
        exit /b 1
    )
    echo       Dependencias instaladas.
) else (
    echo       Tudo ja instalado.
)

REM ---- 4. Criar .env ----------------------------------------------
if not exist ".env" (
    echo [4/6] Criando .env com chave gerada automaticamente...
    for /f %%K in ('.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"') do set "JWT_KEY=%%K"
    (
        echo JWT_SECRET_KEY=!JWT_KEY!
        echo DATABASE_URL=mysql+pymysql://root:@localhost:3306/atalaia
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
        echo.
        echo # Credenciais dos usuarios de demonstracao
        echo USUARIO_TESTE_GESTOR_EMAIL=gestor@atalaia.com
        echo USUARIO_TESTE_GESTOR_SENHA=Gestor@2024
        echo USUARIO_TESTE_SUPERVISOR_EMAIL=supervisor@atalaia.com
        echo USUARIO_TESTE_SUPERVISOR_SENHA=Superv@2024
        echo USUARIO_TESTE_TECNICO_EMAIL=tecnico@atalaia.com
        echo USUARIO_TESTE_TECNICO_SENHA=Tecnico@2024
    ) > .env
    echo       Arquivo .env criado.
) else (
    echo [4/6] Arquivo .env encontrado.
)

REM ---- 5. Preparar banco e usuarios -------------------------------
echo [5/6] Preparando banco de dados e usuarios de teste...
.venv\Scripts\python.exe criar_usuarios_teste.py --auto
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel preparar o banco de dados.
    echo        Se estiver usando o XAMPP: abra o painel e clique em "Start"
    echo        ao lado de MySQL. Depois execute este arquivo novamente.
    echo        Se o banco "atalaia" nao existir: acesse o phpMyAdmin e
    echo        crie um banco com o nome exato "atalaia".
    pause
    exit /b 1
)

REM ---- 6. Iniciar servidor ----------------------------------------
echo [6/6] Iniciando servidor...
echo.
echo  Acesse: http://localhost:5000
echo  Para encerrar: pressione Ctrl+C nesta janela.
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"
.venv\Scripts\python.exe run.py

pause
