"""
Script de criacao de usuarios de teste.
Uso: python criar_usuarios_teste.py

Cria um usuario para cada perfil (Gestor, Supervisor, Tecnico).
Se nao informar senha no terminal, uma senha forte e gerada e exibida UMA vez.
Nenhuma senha fica salva no codigo.
"""
import sys
import secrets
import string
import getpass
import bcrypt
from dotenv import load_dotenv

load_dotenv()

from app.config import Config
from src.database import inicializar_banco, abrir_sessao, Base, obter_engine
from src.models import Usuario, CargoEnum, StatusContaEnum

# Importa todos os models para o SQLAlchemy criar as tabelas
from src.models import (  # noqa: F401
    Setor, Camera, Incidente, TipoInfracao, NotificacaoPush, Log
)


def gerar_senha_aleatoria(tamanho: int = 16) -> str:
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(caracteres) for _ in range(tamanho))


def criar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


USUARIOS_TESTE = [
    {
        "cpf": "000.000.001-01",
        "nome": "Ana Souza",
        "email": "gestor@atalaia.com",
        "cargo": CargoEnum.Gestor,
    },
    {
        "cpf": "000.000.002-02",
        "nome": "Rafael Mendes",
        "email": "supervisor@atalaia.com",
        "cargo": CargoEnum.Supervisor,
    },
    {
        "cpf": "000.000.003-03",
        "nome": "Carlos Lima",
        "email": "tecnico@atalaia.com",
        "cargo": CargoEnum.Tecnico,
    },
]


def main():
    inicializar_banco(Config.DATABASE_URL)

    # Cria as tabelas se nao existirem
    Base.metadata.create_all(bind=obter_engine())

    print("\n=== Criacao de Usuarios de Teste — ATALAIA 4.0 ===\n")
    print("Deixe o campo em branco para gerar senha automatica.\n")

    sessao = abrir_sessao()
    try:
        for dados in USUARIOS_TESTE:
            cargo_nome = dados["cargo"].value
            email = dados["email"]

            # Verifica se ja existe
            existente = sessao.query(Usuario).filter(Usuario.email == email).first()
            if existente:
                print(f"[{cargo_nome}] {email} ja existe — ignorando.")
                continue

            # Pede a senha no terminal (sem eco)
            entrada = getpass.getpass(f"Senha para {cargo_nome} ({email}) [Enter = gerar]: ")
            if entrada.strip():
                senha = entrada.strip()
                exibir_senha = False
            else:
                senha = gerar_senha_aleatoria()
                exibir_senha = True

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

            if exibir_senha:
                print(f"  [{cargo_nome}] criado — senha (guarde agora): {senha}")
            else:
                print(f"  [{cargo_nome}] criado com a senha informada.")

    finally:
        sessao.close()

    print("\nPronto. Para logar, use os e-mails acima em /login.\n")


if __name__ == "__main__":
    main()
