"""
Testes do logout nos tres perfis, com a protecao CSRF LIGADA (como em producao).
"""
import pytest

PERFIS = [
    ("gestor", "gestor_email", "/gestor"),
    ("supervisor", "supervisor_email", "/supervisor"),
    ("tecnico", "tecnico_email", "/tecnico"),
]


def _entrar(cliente, usuarios_teste, chave_email):
    r = cliente.post("/login", data={
        "email": usuarios_teste[chave_email],
        "senha_hash": usuarios_teste["senha"],
    })
    assert r.status_code == 302
    return r


def _token_csrf(cliente):
    cookie = cliente.get_cookie("csrf_access_token")
    assert cookie is not None, "cookie csrf_access_token nao foi criado no login"
    return cookie.value


@pytest.mark.parametrize("perfil,chave_email,painel", PERFIS)
def test_logout_pelo_formulario_da_pagina(app, usuarios_teste, csrf_ligado, perfil, chave_email, painel):
    """Fluxo real: o navegador envia o token CSRF no campo oculto do formulario."""
    with app.test_client() as c:
        _entrar(c, usuarios_teste, chave_email)
        pagina = c.get(painel).get_data(as_text=True)
        assert 'action="/logout"' in pagina

        r = c.post("/logout", data={"csrf_token": _token_csrf(c)}, follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/login")

        # cookies de acesso e renovacao apagados
        assert c.get_cookie("access_token_cookie") is None
        assert c.get_cookie("refresh_token_cookie") is None

        # mensagem na tela de login
        tela = c.get("/login").get_data(as_text=True)
        assert "Você saiu do sistema" in tela

        # o botao "voltar" nao reabre o painel: sem cookie, volta ao login
        r = c.get(painel, follow_redirects=False)
        assert r.status_code == 302 and "/login" in r.headers["Location"]


@pytest.mark.parametrize("perfil,chave_email,painel", PERFIS)
def test_logout_com_cabecalho_csrf(app, usuarios_teste, csrf_ligado, perfil, chave_email, painel):
    with app.test_client() as c:
        _entrar(c, usuarios_teste, chave_email)
        r = c.post("/logout", headers={"X-CSRF-TOKEN": _token_csrf(c)})
        assert r.status_code == 302
        assert c.get_cookie("access_token_cookie") is None


def test_resposta_do_logout_manda_apagar_os_dois_cookies(app, usuarios_teste, csrf_ligado):
    with app.test_client() as c:
        _entrar(c, usuarios_teste, "gestor_email")
        r = c.post("/logout", data={"csrf_token": _token_csrf(c)})
        cookies = " ".join(r.headers.getlist("Set-Cookie"))
        assert "access_token_cookie=;" in cookies
        assert "refresh_token_cookie=;" in cookies


def test_logout_sem_csrf_nao_derruba_nem_mantem_sessao_quebrada(app, usuarios_teste, csrf_ligado):
    """Mesmo sem o token CSRF, o usuario precisa sair (nada de ficar preso no painel)."""
    with app.test_client() as c:
        _entrar(c, usuarios_teste, "gestor_email")
        r = c.post("/logout", follow_redirects=False)
        assert r.status_code == 302
        assert c.get_cookie("access_token_cookie") is None
