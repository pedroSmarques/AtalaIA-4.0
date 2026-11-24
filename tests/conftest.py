"""
Configuracao dos testes: cria um app de teste com banco SQLite em memoria.
Assim nao e necessario um MySQL rodando para executar os testes.
"""
import pytest
import bcrypt
from app import criar_app
from app.config import Config
from src.database import inicializar_banco, Base, obter_engine, abrir_sessao
from src.models import Usuario, CargoEnum, StatusContaEnum


class ConfigTeste(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    JWT_COOKIE_SECURE = False
    # Desativa CSRF nos testes para simplificar (testamos CSRF separado)
    JWT_COOKIE_CSRF_PROTECT = False
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope="session")
def app():
    aplicacao = criar_app(ConfigTeste)
    with aplicacao.app_context():
        # Cria as tabelas no banco de teste
        from src.models import (  # noqa: F401
            Setor, Camera, Incidente, TipoInfracao, NotificacaoPush, Log
        )
        Base.metadata.create_all(bind=obter_engine())
        yield aplicacao
        Base.metadata.drop_all(bind=obter_engine())


@pytest.fixture(scope="session")
def usuarios_teste(app):
    """Cria um usuario por perfil no banco de teste."""
    with app.app_context():
        sessao = abrir_sessao()
        try:
            usuarios = {}
            for cargo, email, nome in [
                (CargoEnum.Gestor,     "gestor@teste.com",     "Ana Teste"),
                (CargoEnum.Supervisor, "supervisor@teste.com", "Rafael Teste"),
                (CargoEnum.Tecnico,    "tecnico@teste.com",    "Carlos Teste"),
            ]:
                senha_hash = bcrypt.hashpw(b"senha_teste_123", bcrypt.gensalt()).decode()
                u = Usuario(
                    cpf=f"999.999.{cargo.value[:3]}-00",
                    nome=nome,
                    email=email,
                    senha_hash=senha_hash,
                    cargo=cargo,
                    status_conta=StatusContaEnum.ativo,
                )
                sessao.add(u)
            sessao.commit()
            usuarios["gestor_email"] = "gestor@teste.com"
            usuarios["supervisor_email"] = "supervisor@teste.com"
            usuarios["tecnico_email"] = "tecnico@teste.com"
            usuarios["senha"] = "senha_teste_123"
            return usuarios
        finally:
            sessao.close()


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def csrf_ligado(app):
    """Liga a protecao CSRF do JWT so durante o teste (por padrao os testes a desligam)."""
    anterior = app.config["JWT_COOKIE_CSRF_PROTECT"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    yield
    app.config["JWT_COOKIE_CSRF_PROTECT"] = anterior


def entrar(cliente, email, senha="senha_teste_123"):
    """Faz login pelo formulario e devolve a resposta (espera redirecionamento)."""
    r = cliente.post("/login", data={"email": email, "senha_hash": senha})
    assert r.status_code == 302, f"login falhou para {email}: {r.status_code}"
    return r
