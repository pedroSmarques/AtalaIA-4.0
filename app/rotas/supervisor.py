from flask import Blueprint, render_template, abort
from flask_jwt_extended import get_jwt, get_jwt_identity
from app.autenticacao.decoradores import perfil_requerido
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO
from src.dao.camera_dao import CameraDAO
from src.dao.incidente_dao import IncidenteDAO
from src.models import StatusCameraEnum, StatusAtendimentoEnum

supervisor_bp = Blueprint("supervisor", __name__, url_prefix="/supervisor")


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


@supervisor_bp.route("/")
@supervisor_bp.route("")
@perfil_requerido("Supervisor")
def dashboard():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        cam_dao = CameraDAO(sessao)
        inc_dao = IncidenteDAO(sessao)

        todas_cameras = cam_dao.listar_todas()
        cameras_ativas = sum(1 for c in todas_cameras if c.status == StatusCameraEnum.ativa)

        pendentes = inc_dao.listar_pendentes()
        em_atendimento = inc_dao.listar_por_status(StatusAtendimentoEnum.em_atendimento)
        resolvidos_hoje = inc_dao.contar_resolvidos_hoje()

        ctx.update({
            "cameras_ativas": cameras_ativas,
            "cameras_total": len(todas_cameras),
            "incidentes_pendentes": pendentes,
            "incidentes_pendentes_count": len(pendentes),
            "incidentes_em_atendimento": len(em_atendimento),
            "incidentes_resolvidos_hoje": resolvidos_hoje,
        })
    finally:
        sessao.close()
    return render_template("supervisor/dashboard.html", **ctx)


@supervisor_bp.route("/alertas")
@perfil_requerido("Supervisor")
def alertas():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        inc_dao = IncidenteDAO(sessao)
        lista = inc_dao.listar_todos()
        pendentes_count = sum(1 for i in lista if i.status_atendimento == StatusAtendimentoEnum.pendente)
        ctx.update({
            "incidentes": lista,
            "incidentes_pendentes_count": pendentes_count,
        })
    finally:
        sessao.close()
    return render_template("supervisor/alertas.html", **ctx)


@supervisor_bp.route("/alertas/<int:id_incidente>")
@perfil_requerido("Supervisor")
def detalhe(id_incidente: int):
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        inc_dao = IncidenteDAO(sessao)
        incidente = inc_dao.buscar_por_id(id_incidente)
        if not incidente:
            abort(404)
        ctx["incidente"] = incidente
    finally:
        sessao.close()
    return render_template("supervisor/detalhe.html", **ctx)


@supervisor_bp.route("/cameras")
@perfil_requerido("Supervisor")
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
    return render_template("supervisor/cameras.html", **ctx)


@supervisor_bp.route("/relatorio-ia")
@perfil_requerido("Supervisor")
def relatorio_ia():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        inc_dao = IncidenteDAO(sessao)
        ctx["incidentes"] = inc_dao.listar_todos()
    finally:
        sessao.close()
    return render_template("supervisor/relatorio_ia.html", **ctx)
