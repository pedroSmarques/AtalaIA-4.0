from functools import wraps
from flask import redirect, url_for, abort, flash, g
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt, get_jwt_identity,
    create_access_token, set_access_cookies,
)
from flask_jwt_extended.exceptions import NoAuthorizationError, CSRFError
from jwt.exceptions import ExpiredSignatureError


def perfil_requerido(*perfis):
    """
    Decorator que exige login e verifica o cargo do usuario.
    Uso: @perfil_requerido("Gestor") ou @perfil_requerido("Gestor", "Supervisor")
    Sem token valido -> redireciona para /login.
    Cargo errado -> HTTP 403.
    Token de acesso expirado -> tenta renovar com o refresh token.
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            claims = None

            try:
                verify_jwt_in_request(locations=["cookies"])
                claims = get_jwt()
            except ExpiredSignatureError:
                # Tenta renovar o token de acesso usando o refresh token
                try:
                    verify_jwt_in_request(locations=["cookies"], refresh=True)
                    refresh_claims = get_jwt()
                    identidade = get_jwt_identity()
                    novo_token = create_access_token(
                        identity=identidade,
                        additional_claims={"cargo": refresh_claims.get("cargo")},
                    )
                    # Salva na requisicao para aplicar na resposta via after_request
                    g._novo_token_acesso = novo_token
                    claims = refresh_claims
                except Exception:
                    flash("Sua sessao expirou. Faca login novamente.", "aviso")
                    return redirect(url_for("autenticacao.login"))
            except CSRFError:
                # Token CSRF ausente ou invalido: recusa o POST (nao e falta de login)
                abort(403)
            except Exception:
                return redirect(url_for("autenticacao.login"))

            if claims is None or claims.get("cargo") not in perfis:
                abort(403)

            return f(*args, **kwargs)
        return wrapper
    return decorador
