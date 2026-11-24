from flask import Blueprint, render_template
from app.autenticacao.decoradores import perfil_requerido
from app.contexto import contexto_usuario as _contexto_usuario
from src.database import abrir_sessao
from src.dao.camera_dao import CameraDAO
from src.dao.log_dao import LogDAO
from src.models import StatusCameraEnum

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")


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
