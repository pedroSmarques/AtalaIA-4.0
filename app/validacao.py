"""Validacoes de campos de formulario compartilhadas entre as rotas."""
import re

_REGEX_EMAIL = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
_REGEX_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")

SENHA_MINIMA = 8
SENHA_MAXIMA = 72   # limite do bcrypt, em bytes


def email_valido(texto: str) -> bool:
    return bool(texto) and len(texto) <= 100 and bool(_REGEX_EMAIL.match(texto))


def cpf_valido_formato(texto: str) -> bool:
    return bool(_REGEX_CPF.match(texto or ""))


def limpar_texto(texto: str | None) -> str:
    """Tira espacos nas pontas e repetidos no meio."""
    return " ".join((texto or "").split())


def erro_de_senha(senha: str) -> str | None:
    """Mensagem de erro se a senha nao serve; None se estiver ok."""
    if len(senha) < SENHA_MINIMA:
        return f"Use pelo menos {SENHA_MINIMA} caracteres na senha."
    if len(senha.encode("utf-8")) > SENHA_MAXIMA:
        return f"Use no máximo {SENHA_MAXIMA} caracteres na senha."
    return None
