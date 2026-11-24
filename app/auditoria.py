"""Registro de acoes dos usuarios na tabela de logs do sistema."""
from flask import request
from flask_jwt_extended import get_jwt_identity

from src.dao.log_dao import LogDAO
from src.database import abrir_sessao


def registrar_acao(acao: str, detalhes: str = None, tabela: str = None, id_registro: int = None) -> None:
    """Grava no log quem fez o que (usuario do token, IP da requisicao). `acao` tem ate 30 caracteres."""
    sessao = abrir_sessao()
    try:
        LogDAO(sessao).registrar_log(
            acao, request.remote_addr or "desconhecido",
            tabela=tabela, id_registro=id_registro, detalhes=detalhes,
            id_usuario=int(get_jwt_identity()),
        )
    finally:
        sessao.close()
