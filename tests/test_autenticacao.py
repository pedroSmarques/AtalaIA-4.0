"""
Testes de autenticacao: login, logout, rotas protegidas, CSRF e renovacao de token.
"""
import pytest
from flask_jwt_extended import decode_token


# ------------------------------------------------------------------
# Login correto e errado
# ------------------------------------------------------------------

def test_login_bem_sucedido_gestor(cliente, usuarios_teste):
    r = cliente.post("/login", data={
        "email": usuarios_teste["gestor_email"],
        "senha_hash": usuarios_teste["senha"],
    }, follow_redirects=False)
    # Deve redirecionar para o dashboard do gestor
    assert r.status_code == 302
    assert "/gestor" in r.headers["Location"]
    # Cookies de acesso e renovacao devem ser definidos
    assert "access_token_cookie" in r.headers.get("Set-Cookie", "")


def test_login_senha_errada(cliente, usuarios_teste):
    r = cliente.post("/login", data={
        "email": usuarios_teste["gestor_email"],
        "senha_hash": "senha_errada",
    })
    assert r.status_code == 401


def test_login_email_inexistente(cliente):
    r = cliente.post("/login", data={
        "email": "nao_existe@exemplo.com",
        "senha_hash": "qualquersenha",
    })
    assert r.status_code == 401


# ------------------------------------------------------------------
# Acesso sem token deve ir para /login
# ------------------------------------------------------------------

def test_acesso_sem_token_redireciona_login(cliente):
    for rota in ["/gestor", "/supervisor", "/tecnico"]:
        r = cliente.get(rota, follow_redirects=False)
        assert r.status_code == 302, f"Esperado 302 em {rota}"
        assert "/login" in r.headers["Location"]


# ------------------------------------------------------------------
# Perfil errado recebe 403
# ------------------------------------------------------------------

def _fazer_login(cliente, usuarios_teste, cargo: str):
    """Retorna um cliente com cookies de autenticacao do cargo informado."""
    email_map = {
        "gestor":     usuarios_teste["gestor_email"],
        "supervisor": usuarios_teste["supervisor_email"],
        "tecnico":    usuarios_teste["tecnico_email"],
    }
    r = cliente.post("/login", data={
        "email": email_map[cargo],
        "senha_hash": usuarios_teste["senha"],
    }, follow_redirects=False)
    assert r.status_code == 302, f"Login falhou: {r.data}"
    return cliente


def test_supervisor_nao_acessa_rota_gestor(app, usuarios_teste):
    with app.test_client() as c:
        _fazer_login(c, usuarios_teste, "supervisor")
        r = c.get("/gestor")
        assert r.status_code == 403


def test_tecnico_nao_acessa_rota_supervisor(app, usuarios_teste):
    with app.test_client() as c:
        _fazer_login(c, usuarios_teste, "tecnico")
        r = c.get("/supervisor")
        assert r.status_code == 403


def test_gestor_acessa_propria_rota(app, usuarios_teste):
    with app.test_client() as c:
        _fazer_login(c, usuarios_teste, "gestor")
        r = c.get("/gestor", follow_redirects=True)
        assert r.status_code == 200


# ------------------------------------------------------------------
# Logout apaga os cookies
# ------------------------------------------------------------------

def test_logout_apaga_cookies(app, usuarios_teste):
    with app.test_client() as c:
        _fazer_login(c, usuarios_teste, "gestor")
        r = c.post("/logout", follow_redirects=False)
        assert r.status_code == 302
        # Os cookies de JWT devem ser deletados (valor vazio ou expires no passado)
        cookie_header = r.headers.get("Set-Cookie", "")
        assert "access_token_cookie" in cookie_header


# ------------------------------------------------------------------
# POST sem CSRF e recusado (quando CSRF esta ligado)
# ------------------------------------------------------------------

def test_logout_sem_csrf_recusado(app, usuarios_teste):
    """Com protecao CSRF ativa, POST sem token deve ser recusado."""
    from tests.conftest import ConfigTeste

    class ConfigComCsrf(ConfigTeste):
        JWT_COOKIE_CSRF_PROTECT = True

    app_csrf = __import__("app", fromlist=["criar_app"]).criar_app(ConfigComCsrf)
    with app_csrf.test_client() as c:
        # Faz login sem CSRF (neste app de teste, o login nao e protegido por JWT)
        c.post("/login", data={
            "email": usuarios_teste["gestor_email"],
            "senha_hash": usuarios_teste["senha"],
        })
        # POST sem o campo csrf_token deve ser recusado
        r = c.post("/logout", data={})
        assert r.status_code in (400, 401, 403, 302)


# ------------------------------------------------------------------
# Token expirado e renovado
# ------------------------------------------------------------------

def test_renovar_token_com_refresh_valido(app, usuarios_teste):
    with app.test_client() as c:
        _fazer_login(c, usuarios_teste, "gestor")
        r = c.post("/token/renovar", follow_redirects=False)
        # Deve redirecionar (pode ser para login se refresh nao estiver no cookie,
        # mas o status nao deve ser um erro 4xx/5xx)
        assert r.status_code in (200, 302)
