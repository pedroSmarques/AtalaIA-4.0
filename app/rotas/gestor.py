from flask import Blueprint, render_template, abort
from app.autenticacao.decoradores import perfil_requerido
from app.contexto import contexto_usuario as _contexto_usuario
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO
from src.dao.camera_dao import CameraDAO
from src.dao.incidente_dao import IncidenteDAO
from src.dao.log_dao import LogDAO
from src.models import StatusCameraEnum, StatusAtendimentoEnum
from datetime import date

gestor_bp = Blueprint("gestor", __name__, url_prefix="/gestor")


@gestor_bp.route("/")
@gestor_bp.route("")
@perfil_requerido("Gestor")
def inicio():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        cam_dao = CameraDAO(sessao)
        inc_dao = IncidenteDAO(sessao)

        # Consultas existentes nos DAOs
        todas_cameras = cam_dao.listar_todas()
        cameras_ativas = sum(1 for c in todas_cameras if c.status == StatusCameraEnum.ativa)
        cameras_total = len(todas_cameras)

        pendentes = inc_dao.listar_pendentes()
        incidentes_abertos = len(pendentes)
        incidentes_hoje = inc_dao.contar_hoje()
        incidentes_recentes = inc_dao.listar_recentes(limite=5)

        ctx.update({
            "cameras_ativas": cameras_ativas,
            "cameras_total": cameras_total,
            "incidentes_hoje": incidentes_hoje,
            "incidentes_abertos": incidentes_abertos,
            "incidentes_recentes": incidentes_recentes,
            "conformidade_pct": 94,
        })
    finally:
        sessao.close()
    return render_template("gestor/inicio.html", **ctx)


@gestor_bp.route("/alertas")
@perfil_requerido("Gestor")
def alertas():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        inc_dao = IncidenteDAO(sessao)
        lista_incidentes = inc_dao.listar_todos()
        ctx["incidentes"] = lista_incidentes
    finally:
        sessao.close()
    return render_template("gestor/alertas.html", **ctx)


@gestor_bp.route("/alertas/<int:id_incidente>")
@perfil_requerido("Gestor")
def detalhe_alerta(id_incidente: int):
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
    return render_template("gestor/detalhe_alerta.html", **ctx)


@gestor_bp.route("/cameras")
@perfil_requerido("Gestor")
def cameras():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        cam_dao = CameraDAO(sessao)
        lista = cam_dao.listar_todas()
        ativas = sum(1 for c in lista if c.status == StatusCameraEnum.ativa)
        inativas = sum(1 for c in lista if c.status == StatusCameraEnum.inativa)
        manutencao = sum(1 for c in lista if c.status.value == "manutenção")
        ctx.update({
            "cameras": lista,
            "cameras_ativas": ativas,
            "cameras_inativas": inativas,
            "cameras_manutencao": manutencao,
        })
    finally:
        sessao.close()
    return render_template("gestor/cameras.html", **ctx)


@gestor_bp.route("/usuarios")
@perfil_requerido("Gestor")
def usuarios():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        ctx["usuarios"] = dao.listar_todos()
    finally:
        sessao.close()
    return render_template("gestor/usuarios.html", **ctx)


@gestor_bp.route("/setores")
@perfil_requerido("Gestor")
def setores():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        from src.dao.setor_dao import SetorDAO
        dao = SetorDAO(sessao)
        ctx["setores"] = dao.listar_todos()
    finally:
        sessao.close()
    return render_template("gestor/setores.html", **ctx)


@gestor_bp.route("/relatorios")
@perfil_requerido("Gestor")
def relatorios():
    ctx = _contexto_usuario()
    return render_template("gestor/relatorios.html", **ctx)


@gestor_bp.route("/logs")
@perfil_requerido("Gestor")
def logs():
    ctx = _contexto_usuario()
    sessao = abrir_sessao()
    try:
        dao = LogDAO(sessao)
        ctx["logs"] = dao.listar_ultimos_logs(limite=100)
    finally:
        sessao.close()
    return render_template("gestor/logs.html", **ctx)
