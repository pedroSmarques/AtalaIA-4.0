from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.autenticacao.decoradores import perfil_requerido
from app.auditoria import registrar_acao
from app.contexto import contexto_usuario as _contexto_usuario
from app.rotas.gestor import ler_dados_da_camera
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


@tecnico_bp.route("/cameras/<int:id_camera>/editar", methods=["POST"])
@perfil_requerido("Tecnico")
def editar_camera(id_camera: int):
    """O tecnico ajusta so a conexao: URL, FPS e status (codigo e setor ficam com o gestor)."""
    dados, erro = ler_dados_da_camera(request.form, completo=False)
    if erro:
        flash(erro, "erro")
        return redirect(url_for("tecnico.cameras"))
    sessao = abrir_sessao()
    try:
        camera = CameraDAO(sessao).atualizar(id_camera, **dados)
        if not camera:
            abort(404)
        codigo = camera.codigo_identificador
    finally:
        sessao.close()
    registrar_acao("CAMERA_EDITADA", f"{codigo} (ajuste tecnico)", tabela="Camera", id_registro=id_camera)
    flash(f"Câmera {codigo} atualizada.", "sucesso")
    return redirect(url_for("tecnico.cameras"))
