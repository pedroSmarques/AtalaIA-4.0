import bcrypt
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_jwt_extended import get_jwt_identity
from app.autenticacao.decoradores import perfil_requerido
from app.auditoria import registrar_acao
from app.contexto import contexto_usuario as _contexto_usuario
from app.validacao import cpf_valido_formato, email_valido, erro_de_senha, limpar_texto
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO
from src.dao.camera_dao import CameraDAO
from src.dao.incidente_dao import IncidenteDAO
from src.dao.log_dao import LogDAO
from src.dao.setor_dao import SetorDAO
from src.models import (
    CargoEnum, NivelRiscoEnum, StatusAtendimentoEnum, StatusCameraEnum, StatusContaEnum,
)
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
            "setores": SetorDAO(sessao).listar_todos(),
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


# =====================================================================
# Cadastros: usuarios, setores e cameras (POST -> grava -> redireciona com aviso)
# =====================================================================

def _voltar(endpoint: str):
    return redirect(url_for(endpoint))


def _erro(mensagem: str, endpoint: str):
    flash(mensagem, "erro")
    return _voltar(endpoint)


def _valor_enum(enum_cls, texto: str):
    """Converte o texto do formulario para o enum, ou None se nao existir."""
    try:
        return enum_cls(texto)
    except ValueError:
        return None


# ---------- Usuarios ----------

@gestor_bp.route("/usuarios", methods=["POST"])
@perfil_requerido("Gestor")
def criar_usuario():
    nome = limpar_texto(request.form.get("nome"))
    email = (request.form.get("email") or "").strip().lower()
    cpf = (request.form.get("cpf") or "").strip()
    cargo = _valor_enum(CargoEnum, request.form.get("cargo", ""))
    senha = request.form.get("senha", "")

    if not nome or len(nome) > 100:
        return _erro("Informe o nome completo (até 100 caracteres).", "gestor.usuarios")
    if not email_valido(email):
        return _erro("Informe um e-mail válido, como nome@empresa.com.", "gestor.usuarios")
    if not cpf_valido_formato(cpf):
        return _erro("Informe o CPF completo: 000.000.000-00.", "gestor.usuarios")
    if cargo is None:
        return _erro("Escolha o cargo.", "gestor.usuarios")
    mensagem = erro_de_senha(senha)
    if mensagem:
        return _erro(mensagem, "gestor.usuarios")

    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        if dao.buscar_por_email(email):
            return _erro("Já existe um usuário com este e-mail.", "gestor.usuarios")
        if dao.buscar_por_cpf(cpf):
            return _erro("Já existe um usuário com este CPF.", "gestor.usuarios")
        senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        novo = dao.criar(cpf, nome, email, senha_hash, cargo, StatusContaEnum.ativo)
        id_novo = novo.id_usuario
    finally:
        sessao.close()
    registrar_acao("USUARIO_CRIADO", f"{email} ({cargo.value})", tabela="Usuarios", id_registro=id_novo)
    flash(f"Usuário {nome} criado.", "sucesso")
    return _voltar("gestor.usuarios")


@gestor_bp.route("/usuarios/<int:id_usuario>/editar", methods=["POST"])
@perfil_requerido("Gestor")
def editar_usuario(id_usuario: int):
    nome = limpar_texto(request.form.get("nome"))
    email = (request.form.get("email") or "").strip().lower()
    cargo = _valor_enum(CargoEnum, request.form.get("cargo", ""))
    status = _valor_enum(StatusContaEnum, request.form.get("status_conta", ""))

    if not nome or len(nome) > 100:
        return _erro("Informe o nome completo (até 100 caracteres).", "gestor.usuarios")
    if not email_valido(email):
        return _erro("Informe um e-mail válido, como nome@empresa.com.", "gestor.usuarios")
    if cargo is None or status is None:
        return _erro("Escolha o cargo e a situação da conta.", "gestor.usuarios")

    # evita o gestor se trancar para fora do proprio sistema
    if id_usuario == int(get_jwt_identity()) and (cargo != CargoEnum.Gestor or status != StatusContaEnum.ativo):
        return _erro("Você não pode mudar o seu próprio cargo nem bloquear a sua conta.", "gestor.usuarios")

    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        if not dao.buscar_por_id(id_usuario):
            abort(404)
        outro = dao.buscar_por_email(email)
        if outro and outro.id_usuario != id_usuario:
            return _erro("Já existe um usuário com este e-mail.", "gestor.usuarios")
        dao.atualizar(id_usuario, nome, email, cargo, status)
    finally:
        sessao.close()
    registrar_acao("USUARIO_EDITADO", f"{email} ({cargo.value}, {status.value})", tabela="Usuarios", id_registro=id_usuario)
    flash("Usuário atualizado.", "sucesso")
    return _voltar("gestor.usuarios")


@gestor_bp.route("/usuarios/<int:id_usuario>/status", methods=["POST"])
@perfil_requerido("Gestor")
def alterar_status_usuario(id_usuario: int):
    """Bloqueia ou desbloqueia a conta (um bloqueado nao consegue entrar)."""
    status = _valor_enum(StatusContaEnum, request.form.get("status", ""))
    if status not in (StatusContaEnum.ativo, StatusContaEnum.bloqueado):
        abort(400)
    if id_usuario == int(get_jwt_identity()):
        return _erro("Você não pode bloquear a sua própria conta.", "gestor.usuarios")

    sessao = abrir_sessao()
    try:
        usuario = UsuarioDAO(sessao).atualizar_status(id_usuario, status)
        if not usuario:
            abort(404)
        nome = usuario.nome
    finally:
        sessao.close()
    acao = "USUARIO_BLOQUEADO" if status == StatusContaEnum.bloqueado else "USUARIO_DESBLOQUEADO"
    registrar_acao(acao, nome, tabela="Usuarios", id_registro=id_usuario)
    flash(f"{nome} foi {'bloqueado' if status == StatusContaEnum.bloqueado else 'desbloqueado'}.", "sucesso")
    return _voltar("gestor.usuarios")


# ---------- Setores ----------

def _ler_setor():
    nome = limpar_texto(request.form.get("nome_setor"))
    descricao = (request.form.get("descricao") or "").strip() or None
    nivel = _valor_enum(NivelRiscoEnum, request.form.get("nivel_risco", ""))
    if not nome or len(nome) > 50:
        return None, "Informe o nome do setor (até 50 caracteres)."
    if nivel is None:
        return None, "Escolha o nível de risco."
    if descricao and len(descricao) > 1000:
        return None, "A descrição pode ter no máximo 1000 caracteres."
    return (nome, nivel, descricao), None


@gestor_bp.route("/setores", methods=["POST"])
@perfil_requerido("Gestor")
def criar_setor():
    dados, erro = _ler_setor()
    if erro:
        return _erro(erro, "gestor.setores")
    nome, nivel, descricao = dados
    sessao = abrir_sessao()
    try:
        novo = SetorDAO(sessao).criar(nome, nivel, descricao)
        id_novo = novo.id_setor
    finally:
        sessao.close()
    registrar_acao("SETOR_CRIADO", nome, tabela="Setor", id_registro=id_novo)
    flash(f"Setor {nome} criado.", "sucesso")
    return _voltar("gestor.setores")


@gestor_bp.route("/setores/<int:id_setor>/editar", methods=["POST"])
@perfil_requerido("Gestor")
def editar_setor(id_setor: int):
    dados, erro = _ler_setor()
    if erro:
        return _erro(erro, "gestor.setores")
    nome, nivel, descricao = dados
    sessao = abrir_sessao()
    try:
        if not SetorDAO(sessao).atualizar(id_setor, nome, nivel, descricao):
            abort(404)
    finally:
        sessao.close()
    registrar_acao("SETOR_EDITADO", nome, tabela="Setor", id_registro=id_setor)
    flash("Setor atualizado.", "sucesso")
    return _voltar("gestor.setores")


# ---------- Cameras ----------

def ler_dados_da_camera(form, completo: bool = True):
    """
    Valida os campos de camera. completo=True inclui codigo e setor (gestor);
    completo=False so URL, FPS e status (tecnico). Devolve (dict, erro).
    """
    url = (form.get("url_rtsp_stream") or "").strip()
    status = _valor_enum(StatusCameraEnum, form.get("status", ""))
    try:
        fps = int(form.get("fps_operacao", ""))
    except ValueError:
        fps = 0
    if not url or len(url) > 512 or not url.lower().startswith(("rtsp://", "rtsps://", "http://", "https://")):
        return None, "Informe a URL do stream, começando com rtsp://, rtsps://, http:// ou https://."
    if not 1 <= fps <= 60:
        return None, "O FPS deve ser um número entre 1 e 60."
    if status is None:
        return None, "Escolha o status da câmera."
    dados = {"url_rtsp_stream": url, "fps_operacao": fps, "status": status}
    if completo:
        codigo = limpar_texto(form.get("codigo_identificador"))
        if not codigo or len(codigo) > 50:
            return None, "Informe o código da câmera (até 50 caracteres)."
        try:
            id_setor = int(form.get("setor", ""))
        except ValueError:
            return None, "Escolha o setor da câmera."
        dados["codigo_identificador"] = codigo
        dados["fk_Setor_id_setor"] = id_setor
    return dados, None


@gestor_bp.route("/cameras", methods=["POST"])
@perfil_requerido("Gestor")
def criar_camera():
    dados, erro = ler_dados_da_camera(request.form)
    if erro:
        return _erro(erro, "gestor.cameras")
    sessao = abrir_sessao()
    try:
        if not SetorDAO(sessao).buscar_por_id(dados["fk_Setor_id_setor"]):
            return _erro("O setor escolhido não existe.", "gestor.cameras")
        if CameraDAO(sessao).buscar_por_codigo(dados["codigo_identificador"]):
            return _erro("Já existe uma câmera com este código.", "gestor.cameras")
        nova = CameraDAO(sessao).criar(
            dados["codigo_identificador"], dados["url_rtsp_stream"], dados["status"],
            dados["fps_operacao"], dados["fk_Setor_id_setor"],
        )
        id_nova = nova.id_camera
    finally:
        sessao.close()
    registrar_acao("CAMERA_CRIADA", dados["codigo_identificador"], tabela="Camera", id_registro=id_nova)
    flash(f"Câmera {dados['codigo_identificador']} criada.", "sucesso")
    return _voltar("gestor.cameras")


@gestor_bp.route("/cameras/<int:id_camera>/editar", methods=["POST"])
@perfil_requerido("Gestor")
def editar_camera(id_camera: int):
    dados, erro = ler_dados_da_camera(request.form)
    if erro:
        return _erro(erro, "gestor.cameras")
    sessao = abrir_sessao()
    try:
        dao = CameraDAO(sessao)
        if not dao.buscar_por_id(id_camera):
            abort(404)
        if not SetorDAO(sessao).buscar_por_id(dados["fk_Setor_id_setor"]):
            return _erro("O setor escolhido não existe.", "gestor.cameras")
        outra = dao.buscar_por_codigo(dados["codigo_identificador"])
        if outra and outra.id_camera != id_camera:
            return _erro("Já existe uma câmera com este código.", "gestor.cameras")
        dao.atualizar(id_camera, **dados)
    finally:
        sessao.close()
    registrar_acao("CAMERA_EDITADA", dados["codigo_identificador"], tabela="Camera", id_registro=id_camera)
    flash("Câmera atualizada.", "sucesso")
    return _voltar("gestor.cameras")
