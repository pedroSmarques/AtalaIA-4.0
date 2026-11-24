"""
Dados do usuario logado que todo template precisa (cabecalho, menu, avatar).
Antes cada Blueprint tinha a sua copia desta funcao.
"""
from flask import url_for
from flask_jwt_extended import get_jwt, get_jwt_identity
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO


def iniciais_do_nome(nome: str) -> str:
    """'Maria da Silva' -> 'MD' (primeiras letras das duas primeiras palavras)."""
    partes = (nome or "").split()[:2]
    return "".join(p[0].upper() for p in partes) or "??"


def url_da_foto(arquivo: str | None) -> str | None:
    """Nome do arquivo guardado no banco -> URL publica (ou None se nao houver foto)."""
    if not arquivo:
        return None
    return url_for("static", filename=f"uploads/avatares/{arquivo}")


def contexto_usuario() -> dict:
    """Monta o dicionario com os dados do usuario logado para os templates."""
    claims = get_jwt()
    id_usuario, nome, foto = int(get_jwt_identity()), "", None
    sessao = abrir_sessao()
    try:
        usuario = UsuarioDAO(sessao).buscar_por_id(id_usuario)
        if usuario:
            nome, foto = usuario.nome, usuario.foto_perfil
    finally:
        sessao.close()
    return {
        "usuario_id": id_usuario,
        "usuario_nome": nome,
        "usuario_cargo": claims.get("cargo", ""),
        "usuario_iniciais": iniciais_do_nome(nome),
        "usuario_foto": url_da_foto(foto),
    }
