import os
from flask import Flask, g, request
from flask_jwt_extended import JWTManager, set_access_cookies, get_csrf_token
from app.config import Config
from src.database import inicializar_banco

jwt = JWTManager()


def criar_app(config_class=Config):
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(raiz, "src", "views"),
        static_folder=os.path.join(raiz, "static"),
    )
    app.config.from_object(config_class)

    # Inicializa o banco de dados
    inicializar_banco(app.config["DATABASE_URL"])

    # Inicializa extensoes
    jwt.init_app(app)

    # Registra Blueprints
    from app.autenticacao.rotas import autenticacao_bp
    from app.rotas.gestor import gestor_bp
    from app.rotas.supervisor import supervisor_bp
    from app.rotas.tecnico import tecnico_bp

    app.register_blueprint(autenticacao_bp)
    app.register_blueprint(gestor_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(tecnico_bp)

    # Rota raiz -> redireciona para login
    @app.route("/")
    def raiz():
        from flask import redirect, url_for
        return redirect(url_for("autenticacao.login"))

    # Registra handlers de erro
    from app.erros import registrar_handlers_erro
    registrar_handlers_erro(app)

    # Injeta o token CSRF do cookie nos templates para uso em formularios POST
    @app.context_processor
    def injetar_csrf():
        # Se o token de acesso foi renovado nesta requisicao, o CSRF valido e o do token novo
        novo = getattr(g, "_novo_token_acesso", None)
        if novo:
            return {"csrf_token": get_csrf_token(novo)}
        return {"csrf_token": request.cookies.get("csrf_access_token", "")}

    # Aplica novo token de acesso na resposta quando o decorator o tiver renovado
    @app.after_request
    def aplicar_novo_token(resposta):
        novo = getattr(g, "_novo_token_acesso", None)
        if novo:
            set_access_cookies(resposta, novo)
        # Telas autenticadas nunca ficam em cache: o botao "voltar" depois do logout
        # nao pode reabrir o painel a partir do cache do navegador.
        if request.blueprint in ("gestor", "supervisor", "tecnico", "autenticacao"):
            resposta.headers["Cache-Control"] = "no-store, max-age=0"
            resposta.headers["Pragma"] = "no-cache"
        return resposta

    return app
