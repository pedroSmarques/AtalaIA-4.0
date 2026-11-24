"""
Script de criacao de usuarios de teste.

Modos de uso:
  python criar_usuarios_teste.py           — interativo: pede cada senha no terminal
  python criar_usuarios_teste.py --auto    — automatico: usa senhas do .env sem perguntar
  python criar_usuarios_teste.py --resetar — apaga e recria os tres usuarios com senhas do .env

ATENCAO (modo interativo): a digitacao da senha fica INVISIVEL no terminal.
Isso e normal — e um recurso de seguranca do sistema operacional. Pressione Enter
sem digitar nada para gerar uma senha forte automaticamente.
"""
import sys
import secrets
import string
import getpass
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

from app.config import Config
from src.database import inicializar_banco, abrir_sessao, Base, obter_engine, garantir_colunas_novas
from src.models import Usuario, CargoEnum, StatusContaEnum
from src.models import (  # noqa: F401
    Setor, Camera, Incidente, TipoInfracao, NotificacaoPush, Log
)


def gerar_senha_aleatoria(tamanho: int = 16) -> str:
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(caracteres) for _ in range(tamanho))


def criar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


USUARIOS_TEMPLATE = [
    {
        "cpf": "000.000.001-01",
        "nome": "Ana Souza",
        "cargo": CargoEnum.Gestor,
        "env_email": "USUARIO_TESTE_GESTOR_EMAIL",
        "env_senha": "USUARIO_TESTE_GESTOR_SENHA",
        "email_padrao": "gestor@atalaia.com",
    },
    {
        "cpf": "000.000.002-02",
        "nome": "Rafael Mendes",
        "cargo": CargoEnum.Supervisor,
        "env_email": "USUARIO_TESTE_SUPERVISOR_EMAIL",
        "env_senha": "USUARIO_TESTE_SUPERVISOR_SENHA",
        "email_padrao": "supervisor@atalaia.com",
    },
    {
        "cpf": "000.000.003-03",
        "nome": "Carlos Lima",
        "cargo": CargoEnum.Tecnico,
        "env_email": "USUARIO_TESTE_TECNICO_EMAIL",
        "env_senha": "USUARIO_TESTE_TECNICO_SENHA",
        "email_padrao": "tecnico@atalaia.com",
    },
]


def obter_dados_usuarios():
    return [
        {
            "cpf": t["cpf"],
            "nome": t["nome"],
            "cargo": t["cargo"],
            "email": os.environ.get(t["env_email"], t["email_padrao"]),
            "senha_env": os.environ.get(t["env_senha"]),
        }
        for t in USUARIOS_TEMPLATE
    ]


def exibir_tabela(credenciais):
    print()
    print("=" * 62)
    print("   ACESSOS DE DEMONSTRACAO — ATALAIA 4.0")
    print("=" * 62)
    print(f"   {'Perfil':<12} {'E-mail':<30} Senha")
    print("   " + "-" * 57)
    for c in credenciais:
        print(f"   {c['cargo']:<12} {c['email']:<30} {c['senha']}")
    print("=" * 62)
    print()


def main():
    modo_auto = "--auto" in sys.argv
    modo_resetar = "--resetar" in sys.argv

    try:
        inicializar_banco(Config.DATABASE_URL)
        Base.metadata.create_all(bind=obter_engine())
        garantir_colunas_novas()
    except Exception as exc:
        msg = str(exc).lower()
        print()
        if "can't connect" in msg or "connection refused" in msg or "2003" in msg:
            print("[ERRO] Nao foi possivel conectar ao MySQL.")
            print("       No XAMPP: clique em 'Start' ao lado de MySQL.")
        elif "unknown database" in msg or "1049" in msg:
            print("[ERRO] O banco de dados 'atalaia' nao existe.")
            print("       No phpMyAdmin: crie um banco com o nome exato 'atalaia'.")
        else:
            print(f"[ERRO] Falha no banco de dados: {exc}")
        sys.exit(1)

    if not modo_auto and not modo_resetar:
        print("\n=== Criacao de Usuarios de Teste — ATALAIA 4.0 ===\n")
        print("ATENCAO: a digitacao da senha fica INVISIVEL no terminal.")
        print("(Isso e normal — pressione Enter para gerar senha automatica.)\n")

    sessao = abrir_sessao()
    credenciais_finais = []

    try:
        usuarios = obter_dados_usuarios()

        for dados in usuarios:
            cargo_nome = dados["cargo"].value
            email = dados["email"]
            senha_env = dados["senha_env"]

            if modo_resetar:
                existente = sessao.query(Usuario).filter(Usuario.email == email).first()
                if existente:
                    sessao.delete(existente)
                    sessao.commit()

            existente = sessao.query(Usuario).filter(Usuario.email == email).first()
            if existente:
                credenciais_finais.append({
                    "cargo": cargo_nome,
                    "email": email,
                    "senha": senha_env or "(ver .env)",
                })
                if not modo_auto and not modo_resetar:
                    print(f"[{cargo_nome}] {email} ja existe — ignorando.")
                continue

            # Determinar senha
            if senha_env:
                senha = senha_env
            elif modo_auto or modo_resetar:
                senha = gerar_senha_aleatoria()
            else:
                entrada = getpass.getpass(f"Senha para {cargo_nome} ({email}) [Enter = gerar]: ")
                senha = entrada.strip() if entrada.strip() else gerar_senha_aleatoria()

            novo = Usuario(
                cpf=dados["cpf"],
                nome=dados["nome"],
                email=email,
                senha_hash=criar_hash(senha),
                cargo=dados["cargo"],
                status_conta=StatusContaEnum.ativo,
            )
            sessao.add(novo)
            sessao.commit()

            credenciais_finais.append({
                "cargo": cargo_nome,
                "email": email,
                "senha": senha,
            })

            if not modo_auto and not modo_resetar:
                print()
                print(f"  >>> SENHA GERADA — {cargo_nome} ({email}): {senha} <<<")
                print()

    finally:
        sessao.close()

    exibir_tabela(credenciais_finais)

    if not modo_auto and not modo_resetar:
        print("Para logar, acesse /login com os dados acima.\n")


if __name__ == "__main__":
    main()
