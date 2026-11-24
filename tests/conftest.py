"""
Configuracao dos testes: cria um app de teste com banco SQLite em memoria.
Assim nao e necessario um MySQL rodando para executar os testes.
"""
import pytest
import bcrypt
from datetime import datetime, timedelta
from app import criar_app
from app.config import Config
from src.database import inicializar_banco, Base, obter_engine, abrir_sessao
from src.models import (
    Usuario, CargoEnum, StatusContaEnum, Setor, Camera, Incidente, TipoInfracao,
    NivelRiscoEnum, GravidadeEnum, StatusAtendimentoEnum, StatusCameraEnum,
)


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


@pytest.fixture(scope="session")
def dados_de_exemplo(app):
    """Um setor, duas cameras, um tipo de infracao e alguns incidentes recentes."""
    sessao = abrir_sessao()
    try:
        setor = Setor(nome_setor="Linha de Montagem", descricao="", nivel_risco=NivelRiscoEnum.alto)
        tipo = TipoInfracao(nome="Capacete ausente", gravidade=GravidadeEnum.grave)
        sessao.add_all([setor, tipo])
        sessao.flush()
        cam1 = Camera(codigo_identificador="CAM-01", url_rtsp_stream="rtsp://x/1",
                      status=StatusCameraEnum.ativa, fps_operacao=15, fk_Setor_id_setor=setor.id_setor)
        cam2 = Camera(codigo_identificador="CAM-02", url_rtsp_stream="rtsp://x/2",
                      status=StatusCameraEnum.manutencao, fps_operacao=10, fk_Setor_id_setor=setor.id_setor)
        sessao.add_all([cam1, cam2])
        sessao.flush()
        for n, status in enumerate([StatusAtendimentoEnum.pendente, StatusAtendimentoEnum.resolvido,
                                    StatusAtendimentoEnum.falso_positivo]):
            sessao.add(Incidente(
                data_hora_deteccao=datetime.now() - timedelta(days=n + 1), caminho_snapshot="x.jpg",
                confianca_ia=0.9, status_atendimento=status,
                fk_Camera_id_camera=cam1.id_camera, fk_TipoInfracao_id_tipo_infracao=tipo.id_tipo_infracao,
            ))
        sessao.commit()
    finally:
        sessao.close()
