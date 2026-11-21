import bcrypt
from datetime import datetime, timedelta
from collections import defaultdict
from src.database import abrir_sessao
from src.dao.usuario_dao import UsuarioDAO

# Bloqueia apos 5 tentativas erradas em 5 minutos
LIMITE_TENTATIVAS = 5
JANELA_BLOQUEIO = timedelta(minutes=5)

# Dicionario em memoria: IP -> lista de timestamps de falha
_tentativas: dict[str, list[datetime]] = defaultdict(list)


def verificar_bloqueio(identificador: str) -> bool:
    """Retorna True se o IP esta bloqueado por excesso de tentativas."""
    agora = datetime.now()
    # Remove tentativas antigas
    _tentativas[identificador] = [
        t for t in _tentativas[identificador] if agora - t < JANELA_BLOQUEIO
    ]
    return len(_tentativas[identificador]) >= LIMITE_TENTATIVAS


def registrar_falha(identificador: str):
    """Incrementa o contador de tentativas erradas para o IP."""
    _tentativas[identificador].append(datetime.now())


def limpar_tentativas(identificador: str):
    """Limpa o contador apos login bem-sucedido."""
    _tentativas.pop(identificador, None)


def autenticar_usuario(email: str, senha: str):
    """
    Busca o usuario pelo e-mail e verifica a senha bcrypt.
    Retorna o objeto Usuario se valido, None caso contrario.
    """
    sessao = abrir_sessao()
    try:
        dao = UsuarioDAO(sessao)
        usuario = dao.buscar_por_email(email.strip().lower())
        if not usuario:
            return None
        # Rejeita contas bloqueadas ou inativas
        if usuario.status_conta.value in ("bloqueado", "inativo"):
            return None
        # Compara a senha com o hash armazenado
        senha_bytes = senha.encode("utf-8")
        hash_bytes = (
            usuario.senha_hash.encode("utf-8")
            if isinstance(usuario.senha_hash, str)
            else usuario.senha_hash
        )
        if not bcrypt.checkpw(senha_bytes, hash_bytes):
            return None
        return usuario
    finally:
        sessao.close()
