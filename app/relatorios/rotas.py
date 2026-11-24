"""Relatorios em PDF: baixar e enviar por e-mail (envio SIMULADO)."""
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.autenticacao.decoradores import perfil_requerido
from app.contexto import contexto_usuario
from app.relatorios.pdf import gerar_pdf
from app.relatorios.servico import (
    ErroRelatorio, coletar_dados, nome_do_arquivo, validar_destinatario, validar_pedido,
)
from src.dao.log_dao import LogDAO
from src.database import abrir_sessao

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")

TODOS_OS_PERFIS = ("Gestor", "Supervisor", "Tecnico")


def _erro_json(mensagem: str, campo: str = "", status: int = 400):
    return jsonify({"ok": False, "mensagem": mensagem, "campo": campo}), status


def _registrar_log(sessao, acao: str, detalhes: str):
    id_usuario = int(get_jwt_identity())
    LogDAO(sessao).registrar_log(
        acao, request.remote_addr or "desconhecido",
        tabela="Relatorio", detalhes=detalhes, id_usuario=id_usuario,
    )


def _descricao(pedido) -> str:
    return f"{pedido.tipo} de {pedido.inicio.isoformat()} a {pedido.fim.isoformat()}"


@relatorios_bp.route("/pdf", methods=["POST"])
@perfil_requerido(*TODOS_OS_PERFIS)
def baixar():
    """Gera o PDF no servidor e devolve como application/pdf."""
    cargo = get_jwt().get("cargo", "")
    try:
        pedido = validar_pedido(request.form, cargo)
    except ErroRelatorio as e:
        return _erro_json(str(e), e.campo)
    except PermissionError as e:
        return _erro_json(str(e), "tipo", 403)

    ctx = contexto_usuario()
    sessao = abrir_sessao()
    try:
        dados = coletar_dados(sessao, pedido)
        _registrar_log(sessao, "RELATORIO_GERADO", _descricao(pedido))
    finally:
        sessao.close()

    conteudo = gerar_pdf(dados, pedido, gerado_por=ctx["usuario_nome"], cargo=cargo)
    resposta = Response(conteudo, mimetype="application/pdf")
    resposta.headers["Content-Disposition"] = f'attachment; filename="{nome_do_arquivo(pedido)}"'
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@relatorios_bp.route("/email", methods=["POST"])
@perfil_requerido(*TODOS_OS_PERFIS)
def enviar_por_email():
    """
    ENVIO SIMULADO: valida o pedido e o destinatario, gera o relatorio e registra a acao nos
    logs, mas NAO envia e-mail de verdade. O envio real (SMTP ou servico de e-mail) e a
    proxima etapa: troque o bloco marcado abaixo por uma chamada ao servico de envio,
    anexando `conteudo` (o PDF) a mensagem.
    """
    cargo = get_jwt().get("cargo", "")
    try:
        pedido = validar_pedido(request.form, cargo)
        destinatario = validar_destinatario(request.form.get("destinatario"))
    except ErroRelatorio as e:
        return _erro_json(str(e), e.campo)
    except PermissionError as e:
        return _erro_json(str(e), "tipo", 403)

    ctx = contexto_usuario()
    sessao = abrir_sessao()
    try:
        dados = coletar_dados(sessao, pedido)
        conteudo = gerar_pdf(dados, pedido, gerado_por=ctx["usuario_nome"], cargo=cargo)

        # --- SIMULACAO: aqui entraria o envio real (proxima etapa) ---
        # enviar_email(destinatario, assunto=dados["titulo"], anexo=conteudo)
        _ = conteudo
        # -------------------------------------------------------------

        _registrar_log(sessao, "RELATORIO_EMAIL_SIMULADO", f"{_descricao(pedido)} para {destinatario} (simulado)")
    finally:
        sessao.close()

    return jsonify({
        "ok": True,
        "simulado": True,
        "mensagem": f"Relatório enviado para {destinatario}",
    })
