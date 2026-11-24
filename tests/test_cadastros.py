"""
Botoes que antes nao faziam nada: cadastro/edicao de usuarios, setores e cameras (gestor),
ajuste de camera (tecnico) e atendimento de incidente (supervisor).
"""
import bcrypt
import pytest

from src.database import abrir_sessao
from src.models import (
    Camera, Incidente, Log, Setor, StatusAtendimentoEnum, StatusCameraEnum, StatusContaEnum, Usuario,
)
from tests.conftest import entrar


def _logado(app, usuarios_teste, perfil):
    c = app.test_client()
    entrar(c, usuarios_teste[perfil], usuarios_teste["senha"])
    return c


def _um(modelo, **filtros):
    sessao = abrir_sessao()
    try:
        obj = sessao.query(modelo).filter_by(**filtros).first()
        if obj is not None:
            sessao.expunge(obj)
        return obj
    finally:
        sessao.close()


def _acoes_de_log():
    sessao = abrir_sessao()
    try:
        return [l.acao_realizada for l in sessao.query(Log).all()]
    finally:
        sessao.close()


NOVO_USUARIO = {
    "nome": "Paula Nova", "email": "paula.nova@teste.com", "cpf": "123.456.789-09",
    "cargo": "Supervisor", "senha": "SenhaNova@1",
}


# ------------------------------------------------------------------
# Usuarios (gestor)
# ------------------------------------------------------------------

def test_gestor_cria_usuario_que_consegue_entrar(app, usuarios_teste):
    c = _logado(app, usuarios_teste, "gestor_email")
    r = c.post("/gestor/usuarios", data=NOVO_USUARIO)
    assert r.status_code == 302
    u = _um(Usuario, email="paula.nova@teste.com")
    assert u and u.nome == "Paula Nova" and u.cargo.value == "Supervisor"
    assert bcrypt.checkpw(b"SenhaNova@1", u.senha_hash.encode())
    assert "USUARIO_CRIADO" in _acoes_de_log()
    assert app.test_client().post("/login", data={"email": "paula.nova@teste.com", "senha_hash": "SenhaNova@1"}).status_code == 302


@pytest.mark.parametrize("campo,valor", [
    ("nome", "  "), ("email", "sem-arroba"), ("cpf", "12345678909"), ("cargo", "Chefe"), ("senha", "curta"),
])
def test_cria_usuario_rejeita_dados_invalidos(app, usuarios_teste, campo, valor):
    c = _logado(app, usuarios_teste, "gestor_email")
    dados = {**NOVO_USUARIO, "email": f"x_{campo}@teste.com", "cpf": "321.654.987-00", campo: valor}
    r = c.post("/gestor/usuarios", data=dados, follow_redirects=True)
    assert _um(Usuario, email=dados["email"]) is None
    assert 'class="flash flash-erro"' in r.get_data(as_text=True)


def test_nao_cria_usuario_com_email_ou_cpf_repetido(app, usuarios_teste):
    c = _logado(app, usuarios_teste, "gestor_email")
    r = c.post("/gestor/usuarios", data={**NOVO_USUARIO, "email": "gestor@teste.com", "cpf": "111.111.111-11"}, follow_redirects=True)
    assert "Já existe um usuário com este e-mail" in r.get_data(as_text=True)
    r = c.post("/gestor/usuarios", data={**NOVO_USUARIO, "email": "outro@teste.com", "cpf": NOVO_USUARIO["cpf"]}, follow_redirects=True)
    assert "Já existe um usuário com este CPF" in r.get_data(as_text=True)


def test_gestor_edita_e_bloqueia_usuario(app, usuarios_teste):
    c = _logado(app, usuarios_teste, "gestor_email")
    alvo = _um(Usuario, email="paula.nova@teste.com")
    r = c.post(f"/gestor/usuarios/{alvo.id_usuario}/editar", data={
        "nome": "Paula Editada", "email": "paula.nova@teste.com", "cargo": "Tecnico", "status_conta": "ativo"})
    assert r.status_code == 302
    editado = _um(Usuario, id_usuario=alvo.id_usuario)
    assert editado.nome == "Paula Editada" and editado.cargo.value == "Tecnico"

    c.post(f"/gestor/usuarios/{alvo.id_usuario}/status", data={"status": "bloqueado"})
    assert _um(Usuario, id_usuario=alvo.id_usuario).status_conta == StatusContaEnum.bloqueado
    # conta bloqueada nao entra
    assert app.test_client().post("/login", data={"email": "paula.nova@teste.com", "senha_hash": "SenhaNova@1"}).status_code == 401
    c.post(f"/gestor/usuarios/{alvo.id_usuario}/status", data={"status": "ativo"})
    assert _um(Usuario, id_usuario=alvo.id_usuario).status_conta == StatusContaEnum.ativo
    assert {"USUARIO_EDITADO", "USUARIO_BLOQUEADO", "USUARIO_DESBLOQUEADO"} <= set(_acoes_de_log())


def test_gestor_nao_bloqueia_nem_rebaixa_a_si_mesmo(app, usuarios_teste):
    c = _logado(app, usuarios_teste, "gestor_email")
    eu = _um(Usuario, email="gestor@teste.com")
    c.post(f"/gestor/usuarios/{eu.id_usuario}/status", data={"status": "bloqueado"})
    c.post(f"/gestor/usuarios/{eu.id_usuario}/editar", data={
        "nome": eu.nome, "email": eu.email, "cargo": "Tecnico", "status_conta": "ativo"})
    depois = _um(Usuario, id_usuario=eu.id_usuario)
    assert depois.status_conta == StatusContaEnum.ativo and depois.cargo.value == "Gestor"


@pytest.mark.parametrize("perfil", ["supervisor_email", "tecnico_email"])
def test_so_o_gestor_mexe_em_usuarios_setores_e_cameras(app, usuarios_teste, perfil):
    c = _logado(app, usuarios_teste, perfil)
    for rota in ("/gestor/usuarios", "/gestor/usuarios/1/editar", "/gestor/usuarios/1/status",
                 "/gestor/setores", "/gestor/setores/1/editar", "/gestor/cameras", "/gestor/cameras/1/editar"):
        assert c.post(rota, data={"nome": "x"}).status_code == 403, rota


def test_cadastros_exigem_csrf(app, usuarios_teste, csrf_ligado):
    c = _logado(app, usuarios_teste, "gestor_email")
    r = c.post("/gestor/setores", data={"nome_setor": "Sem Token", "nivel_risco": "baixo"})
    assert r.status_code == 403
    assert _um(Setor, nome_setor="Sem Token") is None


# ------------------------------------------------------------------
# Setores e cameras (gestor)
# ------------------------------------------------------------------

def test_gestor_cria_e_edita_setor(app, usuarios_teste):
    c = _logado(app, usuarios_teste, "gestor_email")
    assert c.post("/gestor/setores", data={"nome_setor": "Pintura", "descricao": "Cabine", "nivel_risco": "alto"}).status_code == 302
    s = _um(Setor, nome_setor="Pintura")
    assert s.nivel_risco.value == "alto" and s.descricao == "Cabine"
    c.post(f"/gestor/setores/{s.id_setor}/editar", data={"nome_setor": "Pintura 2", "descricao": "", "nivel_risco": "critico"})
    s2 = _um(Setor, id_setor=s.id_setor)
    assert s2.nome_setor == "Pintura 2" and s2.nivel_risco.value == "critico" and s2.descricao is None
    assert {"SETOR_CRIADO", "SETOR_EDITADO"} <= set(_acoes_de_log())


@pytest.mark.parametrize("dados", [
    {"nome_setor": "", "nivel_risco": "baixo"},
    {"nome_setor": "x" * 51, "nivel_risco": "baixo"},
    {"nome_setor": "Ok", "nivel_risco": "extremo"},
])
def test_setor_invalido_e_recusado(app, usuarios_teste, dados):
    c = _logado(app, usuarios_teste, "gestor_email")
    antes = abrir_sessao().query(Setor).count()
    c.post("/gestor/setores", data=dados)
    assert abrir_sessao().query(Setor).count() == antes


def test_gestor_cria_e_edita_camera(app, usuarios_teste, dados_de_exemplo):
    c = _logado(app, usuarios_teste, "gestor_email")
    setor = _um(Setor, nome_setor="Linha de Montagem")
    dados = {"codigo_identificador": "CAM-99", "setor": str(setor.id_setor),
             "url_rtsp_stream": "rtsp://10.0.0.9:554/s", "fps_operacao": "25", "status": "ativa"}
    assert c.post("/gestor/cameras", data=dados).status_code == 302
    cam = _um(Camera, codigo_identificador="CAM-99")
    assert cam.fps_operacao == 25 and cam.status == StatusCameraEnum.ativa

    c.post(f"/gestor/cameras/{cam.id_camera}/editar", data={**dados, "fps_operacao": "12", "status": "manutenção"})
    cam2 = _um(Camera, id_camera=cam.id_camera)
    assert cam2.fps_operacao == 12 and cam2.status == StatusCameraEnum.manutencao

    # codigo repetido
    r = c.post("/gestor/cameras", data=dados, follow_redirects=True)
    assert "Já existe uma câmera com este código" in r.get_data(as_text=True)


@pytest.mark.parametrize("mudanca", [
    {"fps_operacao": "0"}, {"fps_operacao": "61"}, {"fps_operacao": "abc"},
    {"url_rtsp_stream": "ftp://x"}, {"url_rtsp_stream": ""}, {"status": "quebrada"},
    {"setor": "99999"}, {"codigo_identificador": ""},
])
def test_camera_invalida_e_recusada(app, usuarios_teste, dados_de_exemplo, mudanca):
    c = _logado(app, usuarios_teste, "gestor_email")
    setor = _um(Setor, nome_setor="Linha de Montagem")
    dados = {"codigo_identificador": "CAM-INV", "setor": str(setor.id_setor),
             "url_rtsp_stream": "rtsp://10.0.0.9:554/s", "fps_operacao": "25", "status": "ativa", **mudanca}
    c.post("/gestor/cameras", data=dados)
    assert _um(Camera, codigo_identificador="CAM-INV") is None or dados["codigo_identificador"] != "CAM-INV"


# ------------------------------------------------------------------
# Tecnico: ajusta a conexao da camera
# ------------------------------------------------------------------

def test_tecnico_edita_conexao_da_camera_mas_nao_codigo_nem_setor(app, usuarios_teste, dados_de_exemplo):
    c = _logado(app, usuarios_teste, "tecnico_email")
    cam = _um(Camera, codigo_identificador="CAM-01")
    r = c.post(f"/tecnico/cameras/{cam.id_camera}/editar", data={
        "url_rtsp_stream": "rtsp://novo:554/s", "fps_operacao": "30", "status": "inativa",
        "codigo_identificador": "HACK", "setor": "999"})
    assert r.status_code == 302
    depois = _um(Camera, id_camera=cam.id_camera)
    assert depois.url_rtsp_stream == "rtsp://novo:554/s" and depois.fps_operacao == 30
    assert depois.status == StatusCameraEnum.inativa
    assert depois.codigo_identificador == "CAM-01" and depois.fk_Setor_id_setor == cam.fk_Setor_id_setor


def test_tecnico_com_dado_invalido_nao_altera(app, usuarios_teste, dados_de_exemplo):
    c = _logado(app, usuarios_teste, "tecnico_email")
    cam = _um(Camera, codigo_identificador="CAM-02")
    c.post(f"/tecnico/cameras/{cam.id_camera}/editar", data={"url_rtsp_stream": "rtsp://x", "fps_operacao": "500", "status": "ativa"})
    assert _um(Camera, id_camera=cam.id_camera).fps_operacao == cam.fps_operacao


@pytest.mark.parametrize("perfil", ["gestor_email", "supervisor_email"])
def test_outros_perfis_nao_usam_a_rota_do_tecnico(app, usuarios_teste, dados_de_exemplo, perfil):
    c = _logado(app, usuarios_teste, perfil)
    assert c.post("/tecnico/cameras/1/editar", data={"fps_operacao": "10"}).status_code == 403


# ------------------------------------------------------------------
# Supervisor: atende incidente
# ------------------------------------------------------------------

def _incidente_pendente():
    """Cria um incidente pendente novo (cada teste usa o seu)."""
    from datetime import datetime
    sessao = abrir_sessao()
    try:
        cam = sessao.query(Camera).first()
        tipo = sessao.query(Incidente).first().fk_TipoInfracao_id_tipo_infracao
        inc = Incidente(data_hora_deteccao=datetime.now(), caminho_snapshot="x.jpg", confianca_ia=0.9,
                        status_atendimento=StatusAtendimentoEnum.pendente,
                        fk_Camera_id_camera=cam.id_camera, fk_TipoInfracao_id_tipo_infracao=tipo)
        sessao.add(inc)
        sessao.commit()
        return inc.id_incidente
    finally:
        sessao.close()


def test_supervisor_atende_e_resolve_incidente(app, usuarios_teste, dados_de_exemplo):
    c = _logado(app, usuarios_teste, "supervisor_email")
    id_inc = _incidente_pendente()
    r = c.post(f"/supervisor/alertas/{id_inc}/atendimento", data={"status": "em atendimento", "observacao": "A caminho"})
    assert r.status_code == 302 and f"/supervisor/alertas/{id_inc}" in r.headers["Location"]
    assert _um(Incidente, id_incidente=id_inc).status_atendimento == StatusAtendimentoEnum.em_atendimento

    # a tela agora so oferece encerrar
    html = c.get(f"/supervisor/alertas/{id_inc}").get_data(as_text=True)
    assert "Iniciar atendimento" not in html and "Marcar resolvido" in html

    c.post(f"/supervisor/alertas/{id_inc}/atendimento", data={"status": "resolvido", "observacao": "Corrigido"})
    final = _um(Incidente, id_incidente=id_inc)
    assert final.status_atendimento == StatusAtendimentoEnum.resolvido
    assert final.observacao_atendimento == "Corrigido" and final.data_hora_resolucao is not None
    assert final.fk_Usuarios_id_usuario == _um(Usuario, email="supervisor@teste.com").id_usuario
    assert "INCIDENTE_ATENDIDO" in _acoes_de_log()

    # incidente encerrado nao reabre
    c.post(f"/supervisor/alertas/{id_inc}/atendimento", data={"status": "pendente"})
    assert _um(Incidente, id_incidente=id_inc).status_atendimento == StatusAtendimentoEnum.resolvido


def test_status_invalido_e_perfil_errado(app, usuarios_teste, dados_de_exemplo):
    id_inc = _incidente_pendente()
    c = _logado(app, usuarios_teste, "supervisor_email")
    assert c.post(f"/supervisor/alertas/{id_inc}/atendimento", data={"status": "voando"}).status_code == 400
    assert c.post("/supervisor/alertas/99999/atendimento", data={"status": "resolvido"}).status_code == 404
    for perfil in ("gestor_email", "tecnico_email"):
        outro = _logado(app, usuarios_teste, perfil)
        assert outro.post(f"/supervisor/alertas/{id_inc}/atendimento", data={"status": "resolvido"}).status_code == 403
