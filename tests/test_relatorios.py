"""
Testes dos relatorios em PDF: tipo do conteudo, permissao por perfil, validacao,
envio simulado por e-mail e registro nos logs.
"""
import re
from datetime import datetime, timedelta

import pytest

from src.database import abrir_sessao
from src.models import Camera, Incidente, Log, TipoInfracao
from tests.conftest import entrar

PERIODO = {
    "inicio": (datetime.now() - timedelta(days=10)).date().isoformat(),
    "fim": datetime.now().date().isoformat(),
}


def _form(tipo, **extra):
    return {"tipo": tipo, **PERIODO, **extra}


def _logs(acao):
    sessao = abrir_sessao()
    try:
        return sessao.query(Log).filter(Log.acao_realizada == acao).all()
    finally:
        sessao.close()


# ------------------------------------------------------------------
# PDF
# ------------------------------------------------------------------

@pytest.mark.parametrize("perfil,tipo", [
    ("gestor_email", "incidentes"), ("gestor_email", "cameras"),
    ("supervisor_email", "incidentes"), ("tecnico_email", "cameras"),
])
def test_rota_devolve_pdf(app, usuarios_teste, dados_de_exemplo, perfil, tipo):
    with app.test_client() as c:
        entrar(c, usuarios_teste[perfil], usuarios_teste["senha"])
        r = c.post("/relatorios/pdf", data=_form(tipo, observacoes="Turno da noite sem ocorrências graves."))
        assert r.status_code == 200
        assert r.mimetype == "application/pdf"
        assert r.data.startswith(b"%PDF")
        assert "attachment" in r.headers["Content-Disposition"]
        assert f"atalaia-relatorio-{tipo}-" in r.headers["Content-Disposition"]
        assert r.headers["Cache-Control"].startswith("no-store")


def test_pdf_com_periodo_sem_incidentes_e_observacao_com_emoji(app, usuarios_teste, dados_de_exemplo):
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        r = c.post("/relatorios/pdf", data={
            "tipo": "incidentes", "inicio": "2000-01-01", "fim": "2000-01-31",
            "observacoes": "Sem registros \U0001F600 neste mês — ok",
        })
        assert r.status_code == 200 and r.mimetype == "application/pdf"


def test_pdf_tem_mais_de_uma_pagina_quando_ha_muitos_incidentes(app, usuarios_teste, dados_de_exemplo):
    sessao = abrir_sessao()
    try:
        cam = sessao.query(Camera).first()
        tipo = sessao.query(TipoInfracao).first()
        for n in range(120):
            sessao.add(Incidente(
                data_hora_deteccao=datetime.now() - timedelta(hours=n), caminho_snapshot="x.jpg", confianca_ia=0.8,
                fk_Camera_id_camera=cam.id_camera, fk_TipoInfracao_id_tipo_infracao=tipo.id_tipo_infracao,
            ))
        sessao.commit()
    finally:
        sessao.close()
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        r = c.post("/relatorios/pdf", data=_form("incidentes"))
        assert r.status_code == 200
        assert len(re.findall(rb"/Type\s*/Page[^s]", r.data)) >= 3


# ------------------------------------------------------------------
# Permissao por perfil
# ------------------------------------------------------------------

@pytest.mark.parametrize("perfil,tipo", [
    ("supervisor_email", "cameras"),
    ("tecnico_email", "incidentes"),
])
def test_perfil_sem_permissao_e_recusado(app, usuarios_teste, dados_de_exemplo, perfil, tipo):
    with app.test_client() as c:
        entrar(c, usuarios_teste[perfil], usuarios_teste["senha"])
        for rota in ("/relatorios/pdf", "/relatorios/email"):
            r = c.post(rota, data=_form(tipo, destinatario="alguem@empresa.com"))
            assert r.status_code == 403
            assert r.mimetype == "application/json"
            assert "permissão" in r.get_json()["mensagem"]


def test_sem_login_vai_para_o_login(app):
    with app.test_client() as c:
        for rota in ("/relatorios/pdf", "/relatorios/email"):
            r = c.post(rota, data=_form("incidentes"))
            assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_relatorios_exigem_csrf(app, usuarios_teste, dados_de_exemplo, csrf_ligado):
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        assert c.post("/relatorios/pdf", data=_form("incidentes")).status_code == 403
        token = c.get_cookie("csrf_access_token").value
        r = c.post("/relatorios/pdf", data=_form("incidentes", csrf_token=token))
        assert r.status_code == 200 and r.mimetype == "application/pdf"


def test_modal_so_oferece_os_tipos_do_perfil(app, usuarios_teste):
    esperado = {
        "supervisor_email": ({"incidentes"}, {"cameras"}),
        "tecnico_email": ({"cameras"}, {"incidentes"}),
        "gestor_email": ({"incidentes", "cameras"}, set()),
    }
    paginas = {"supervisor_email": "/supervisor", "tecnico_email": "/tecnico", "gestor_email": "/gestor"}
    for perfil, (presentes, ausentes) in esperado.items():
        with app.test_client() as c:
            entrar(c, usuarios_teste[perfil], usuarios_teste["senha"])
            html = c.get(paginas[perfil]).get_data(as_text=True)
            assert 'id="modalRelatorio"' in html
            for t in presentes:
                assert f'<option value="{t}"' in html
            for t in ausentes:
                assert f'<option value="{t}"' not in html


# ------------------------------------------------------------------
# Validacao
# ------------------------------------------------------------------

@pytest.mark.parametrize("campos,campo_erro", [
    ({"tipo": "inexistente"}, "tipo"),
    ({"inicio": ""}, "inicio"),
    ({"fim": "31/12/2026"}, "fim"),
    ({"inicio": "2026-12-31", "fim": "2026-01-01"}, "fim"),
    ({"inicio": "2020-01-01", "fim": "2026-01-01"}, "fim"),
    ({"observacoes": "x" * 1001}, "observacoes"),
])
def test_validacao_do_pedido(app, usuarios_teste, campos, campo_erro):
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        r = c.post("/relatorios/pdf", data={**_form("incidentes"), **campos})
        assert r.status_code == 400
        assert r.get_json()["campo"] == campo_erro


# ------------------------------------------------------------------
# E-mail (simulado) e logs
# ------------------------------------------------------------------

def test_envio_por_email_simulado_confirma_e_registra_no_log(app, usuarios_teste, dados_de_exemplo):
    antes = len(_logs("RELATORIO_EMAIL_SIMULADO"))
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        r = c.post("/relatorios/email", data=_form("incidentes", destinatario="fulano@empresa.com.br"))
        assert r.status_code == 200
        corpo = r.get_json()
        assert corpo["ok"] is True
        assert corpo["mensagem"] == "Relatório enviado para fulano@empresa.com.br"
    logs = _logs("RELATORIO_EMAIL_SIMULADO")
    assert len(logs) == antes + 1
    assert "fulano@empresa.com.br" in logs[-1].detalhes and "simulado" in logs[-1].detalhes


def test_download_registra_no_log(app, usuarios_teste, dados_de_exemplo):
    antes = len(_logs("RELATORIO_GERADO"))
    with app.test_client() as c:
        entrar(c, usuarios_teste["supervisor_email"], usuarios_teste["senha"])
        assert c.post("/relatorios/pdf", data=_form("incidentes")).status_code == 200
    assert len(_logs("RELATORIO_GERADO")) == antes + 1


@pytest.mark.parametrize("destinatario", [
    "", "   ", "sem-arroba", "a@b", "a b@empresa.com", "fulano@empresa.com\r\nBcc: x@y.com", "@empresa.com",
])
def test_destinatario_invalido_e_recusado_e_nada_e_registrado(app, usuarios_teste, dados_de_exemplo, destinatario):
    antes = len(_logs("RELATORIO_EMAIL_SIMULADO"))
    with app.test_client() as c:
        entrar(c, usuarios_teste["gestor_email"], usuarios_teste["senha"])
        r = c.post("/relatorios/email", data=_form("incidentes", destinatario=destinatario))
        assert r.status_code == 400
        assert r.get_json()["campo"] == "destinatario"
    assert len(_logs("RELATORIO_EMAIL_SIMULADO")) == antes
