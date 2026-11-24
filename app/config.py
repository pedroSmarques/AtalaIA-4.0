import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Chave secreta do Flask (sessoes, flash messages)
    SECRET_KEY = os.environ["JWT_SECRET_KEY"]

    # JWT
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_HTTPONLY = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    # Os formularios HTML enviam o token CSRF no campo oculto "csrf_token".
    # Sem isto o flask-jwt-extended so le o cabecalho X-CSRF-TOKEN e recusa os formularios.
    JWT_CSRF_CHECK_FORM = True

    # Fotos de perfil: a pasta fica dentro de static/ (servida pelo Flask, fora do git)
    PASTA_AVATARES = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads", "avatares"
    )
    # Limite do corpo de qualquer requisicao (a foto aceita e de ate 2 MB; o resto e margem)
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024

    # Banco de dados
    DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/atalaia")
