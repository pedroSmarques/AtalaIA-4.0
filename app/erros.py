from flask import render_template
from flask_jwt_extended.exceptions import NoAuthorizationError


def registrar_handlers_erro(app):
    @app.errorhandler(401)
    def nao_autorizado(e):
        return render_template("erros/401.html"), 401

    @app.errorhandler(403)
    def acesso_negado(e):
        return render_template("erros/403.html"), 403

    @app.errorhandler(413)
    def arquivo_grande(e):
        from flask import flash, redirect, url_for
        flash("O arquivo enviado é grande demais. A foto deve ter no máximo 2 MB.", "erro")
        return redirect(url_for("perfil.meu_perfil"))

    @app.errorhandler(404)
    def nao_encontrado(e):
        return render_template("erros/404.html"), 404

    @app.errorhandler(500)
    def erro_interno(e):
        return render_template("erros/500.html"), 500

    @app.errorhandler(NoAuthorizationError)
    def sem_autorizacao_jwt(e):
        from flask import redirect, url_for
        return redirect(url_for("autenticacao.login"))
