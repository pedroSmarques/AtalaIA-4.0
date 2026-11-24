"""Meu perfil: editar nome, foto e senha. Cada pessoa altera somente o proprio perfil."""
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_jwt_extended import get_jwt_identity
from app.auditoria import registrar_acao
from app.autenticacao.decoradores import perfil_requerido
from app.autenticacao.servico import verificar_bloqueio, registrar_falha, limpar_tentativas
from app.contexto import contexto_usuario
from app.perfil.fotos import ErroFoto, salvar_foto, apagar_foto, processar_foto
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

TODOS_OS_PERFIS = ("Gestor", "Supervisor", "Tecnico")
SENHA_MINIMA = 8
SENHA_MAXIMA = 72   # limite do bcrypt (em bytes)


def _pagina(erros=None, valores=None, status=200):
    """Renderiza a tela com os dados atuais do usuario logado."""
    ctx = contexto_usuario()
    sessao = abrir_sessao()
    try:
        usuario = UsuarioDAO(sessao).buscar_por_id(int(get_jwt_identity()))
        if not usuario:
            abort(404)
        ctx.update({
            "perfil_email": usuario.email,
            "perfil_nome": usuario.nome,
            "perfil_tem_foto": bool(usuario.foto_perfil),
            "perfil_desde": usuario.data_criacao,
        })
    finally:
        sessao.close()
    ctx["erros"] = erros or {}
    ctx["valores"] = valores or {}
    return render_template("perfil/meu_perfil.html", **ctx), status


def _recusar_se_for_outro_usuario():
    """O perfil editado e sempre o do token. Se o formulario tentar apontar para outro, recusa."""
    alvo = request.form.get("id_usuario")
    if alvo is not None and alvo != str(get_jwt_identity()):
        abort(403)


@perfil_bp.route("", methods=["GET"])
@perfil_requerido(*TODOS_OS_PERFIS)
def meu_perfil():
    return _pagina()


@perfil_bp.route("/dados", methods=["POST"])
@perfil_requerido(*TODOS_OS_PERFIS)
def salvar_dados():
    _recusar_se_for_outro_usuario()
    id_usuario = int(get_jwt_identity())
    nome = " ".join(request.form.get("nome", "").split())
    remover = request.form.get("remover_foto") == "1"
    arquivo = request.files.get("foto")
    enviou_foto = bool(arquivo and arquivo.filename)

    erros = {}
    if not nome:
        erros["nome"] = "Informe seu nome."
    elif len(nome) > 100:
        erros["nome"] = "Use no máximo 100 caracteres."

    # Valida a foto ANTES de gravar qualquer coisa; so grava o arquivo se o nome tambem estiver ok
    conteudo_ok = None
    if enviou_foto:
        try:
            conteudo_ok = processar_foto(arquivo)
        except ErroFoto as e:
            erros["foto"] = str(e)

    if erros:
        flash("Corrija os campos destacados.", "erro")
        return _pagina(erros=erros, valores={"nome": nome}, status=400)

    pasta = current_app.config["PASTA_AVATARES"]
    nova_foto = None
    if conteudo_ok is not None:
        arquivo.stream.seek(0)
        nova_foto = salvar_foto(arquivo, pasta)

    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        atual = dao.buscar_por_id(id_usuario)
        if not atual:
            abort(404)
        foto_antiga = atual.foto_perfil
        if nova_foto:
            dao.atualizar_perfil(id_usuario, nome=nome, foto_perfil=nova_foto)
        elif remover:
            dao.atualizar_perfil(id_usuario, nome=nome, foto_perfil=None)
        else:
            dao.atualizar_perfil(id_usuario, nome=nome)
    finally:
        sessao.close()

    if nova_foto or remover:
        apagar_foto(pasta, foto_antiga)

    detalhe = "nome" + (", foto" if nova_foto else "") + (", foto removida" if remover and not nova_foto else "")
    registrar_acao("PERFIL_ATUALIZADO", detalhe, tabela="Usuarios", id_registro=id_usuario)
    flash("Perfil atualizado.", "sucesso")
    return redirect(url_for("perfil.meu_perfil"))


@perfil_bp.route("/senha", methods=["POST"])
@perfil_requerido(*TODOS_OS_PERFIS)
def trocar_senha():
    _recusar_se_for_outro_usuario()
    id_usuario = int(get_jwt_identity())
    chave_bloqueio = f"senha:{id_usuario}"

    atual = request.form.get("senha_atual", "")
    nova = request.form.get("nova_senha", "")
    confirmacao = request.form.get("confirmar_senha", "")

    if verificar_bloqueio(chave_bloqueio):
        flash("Muitas tentativas. Aguarde alguns minutos.", "erro")
        return _pagina(status=429)

    erros = {}
    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        usuario = dao.buscar_por_id(id_usuario)
        if not usuario:
            abort(404)
        hash_atual = usuario.senha_hash.encode("utf-8") if isinstance(usuario.senha_hash, str) else usuario.senha_hash

        if not atual:
            erros["senha_atual"] = "Informe a senha atual."
        elif not bcrypt.checkpw(atual.encode("utf-8"), hash_atual):
            registrar_falha(chave_bloqueio)
            erros["senha_atual"] = "A senha atual não confere."

        if len(nova) < SENHA_MINIMA:
            erros["nova_senha"] = f"Use pelo menos {SENHA_MINIMA} caracteres."
        elif len(nova.encode("utf-8")) > SENHA_MAXIMA:
            erros["nova_senha"] = f"Use no máximo {SENHA_MAXIMA} caracteres."
        elif nova == atual:
            erros["nova_senha"] = "A nova senha deve ser diferente da atual."

        if "nova_senha" not in erros and nova != confirmacao:
            erros["confirmar_senha"] = "A confirmação não é igual à nova senha."

        if erros:
            flash("Corrija os campos destacados.", "erro")
            return _pagina(erros=erros, status=400)

        novo_hash = bcrypt.hashpw(nova.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        dao.atualizar_senha(id_usuario, novo_hash)
    finally:
        sessao.close()

    limpar_tentativas(chave_bloqueio)
    registrar_acao("SENHA_ALTERADA", "Senha alterada pelo proprio usuario", tabela="Usuarios", id_registro=id_usuario)
    flash("Senha alterada.", "sucesso")
    return redirect(url_for("perfil.meu_perfil"))
