from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, make_response, g,
)
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, verify_jwt_in_request, get_jwt, get_jwt_identity,
)
from app.autenticacao.servico import (
    autenticar_usuario, verificar_bloqueio,
    registrar_falha, limpar_tentativas,
)
from app.autenticacao.decoradores import perfil_requerido

autenticacao_bp = Blueprint("autenticacao", __name__)

# Rota de destino apos login por cargo
_DESTINO_POR_CARGO = {
    "Gestor": "gestor.inicio",
    "Supervisor": "supervisor.dashboard",
    "Tecnico": "tecnico.dashboard",
}


@autenticacao_bp.route("/login", methods=["GET", "POST"])
def login():
    # Se ja tem token valido, redireciona direto para o dashboard
    try:
        verify_jwt_in_request(locations=["cookies"], optional=True)
        claims = get_jwt()
        if claims and claims.get("cargo") in _DESTINO_POR_CARGO:
            return redirect(url_for(_DESTINO_POR_CARGO[claims["cargo"]]))
    except Exception:
        pass

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha_hash", "")
        ip = request.remote_addr or "desconhecido"

        if verificar_bloqueio(ip):
            flash("Muitas tentativas. Aguarde alguns minutos.", "erro")
            return render_template("login.html"), 429

        usuario = autenticar_usuario(email, senha)

        if not usuario:
            registrar_falha(ip)
            flash("E-mail ou senha incorretos.", "erro")
            return render_template("login.html"), 401

        limpar_tentativas(ip)

        identidade = str(usuario.id_usuario)
        claims_extras = {"cargo": usuario.cargo.value}

        token_acesso = create_access_token(identity=identidade, additional_claims=claims_extras)
        token_renovacao = create_refresh_token(identity=identidade, additional_claims=claims_extras)

        destino = _DESTINO_POR_CARGO.get(usuario.cargo.value, "autenticacao.login")
        resposta = make_response(redirect(url_for(destino)))
        set_access_cookies(resposta, token_acesso)
        set_refresh_cookies(resposta, token_renovacao)

        primeiro_nome = usuario.nome.split()[0]
        flash(f"Bem-vindo, {primeiro_nome}. Acesso autorizado.", "sucesso")
        return resposta

    return render_template("login.html")


@autenticacao_bp.route("/logout", methods=["POST"])
@perfil_requerido("Gestor", "Supervisor", "Tecnico")
def logout():
    resposta = make_response(redirect(url_for("autenticacao.login")))
    unset_jwt_cookies(resposta)
    flash("Voce saiu com seguranca.", "sucesso")
    return resposta


@autenticacao_bp.route("/token/renovar", methods=["POST"])
def renovar_token():
    """Usa o refresh token para gerar um novo token de acesso."""
    try:
        verify_jwt_in_request(locations=["cookies"], refresh=True)
        claims = get_jwt()
        identidade = get_jwt_identity()

        novo_token = create_access_token(
            identity=identidade,
            additional_claims={"cargo": claims.get("cargo")},
        )
        # Volta para a pagina anterior ou para o login
        pagina_anterior = request.form.get("proxima") or request.referrer or url_for("autenticacao.login")
        resposta = make_response(redirect(pagina_anterior))
        set_access_cookies(resposta, novo_token)
        return resposta
    except Exception:
        resposta = make_response(redirect(url_for("autenticacao.login")))
        unset_jwt_cookies(resposta)
        flash("Sua sessao expirou. Faca login novamente.", "aviso")
        return resposta
