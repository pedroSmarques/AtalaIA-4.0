from flask import Blueprint, render_template
from flask_jwt_extended import get_jwt, get_jwt_identity
from app.autenticacao.decoradores import perfil_requerido
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO
from src.dao.camera_dao import CameraDAO
from src.dao.log_dao import LogDAO
from src.models import StatusCameraEnum

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")


def _contexto_usuario():
    claims = get_jwt()
    nome = ""
    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        usuario = dao.buscar_por_id(int(get_jwt_identity()))
        if usuario:
            nome = usuario.nome
    finally:
        sessao.close()
    iniciais = "".join(p[0].upper() for p in nome.split()[:2]) if nome else "??"
    return {
        "usuario_nome": nome,
        "usuario_cargo": claims.get("cargo", ""),
        "usuario_iniciais": iniciais,
    }


@tecnico_bp.route("/")
@tecnico_bp.route("")
@perfil_requerido("Tecnico")
def dashboard():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        cam_dao = CameraDAO(sessao)
        lista = cam_dao.listar_todas()
        ativas = sum(1 for c in lista if c.status == StatusCameraEnum.ativa)
        inativas = sum(1 for c in lista if c.status == StatusCameraEnum.inativa)
        manutencao = len(lista) - ativas - inativas
        ctx.update({
            "cameras": lista,
            "cameras_ativas": ativas,
            "cameras_inativas": inativas,
            "cameras_manutencao": manutencao,
            "cameras_total": len(lista),
        })
    finally:
        sessao.close()
    return render_template("tecnico/dashboard.html", **ctx)


@tecnico_bp.route("/cameras")
@perfil_requerido("Tecnico")
def cameras():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        cam_dao = CameraDAO(sessao)
        lista = cam_dao.listar_todas()
        ctx.update({
            "cameras": lista,
            "cameras_ativas": sum(1 for c in lista if c.status == StatusCameraEnum.ativa),
            "cameras_total": len(lista),
        })
    finally:
        sessao.close()
    return render_template("tecnico/cameras.html", **ctx)


@tecnico_bp.route("/logs")
@perfil_requerido("Tecnico")
def logs():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        dao = LogDAO(sessao)
        ctx["logs"] = dao.listar_ultimos_logs(limite=100)
    finally:
        sessao.close()
    return render_template("tecnico/logs.html", **ctx)
