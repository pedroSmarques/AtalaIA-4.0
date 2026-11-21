from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Base compartilhada por todos os models — todos precisam importar daqui
class Base(DeclarativeBase):
    pass

_engine = None
_SessaoLocal = None


def inicializar_banco(url_banco: str):
    """Cria o engine e a fabrica de sessoes. Deve ser chamado uma vez ao iniciar o app."""
    global _engine, _SessaoLocal
    _engine = create_engine(url_banco, pool_pre_ping=True)
    _SessaoLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def obter_engine():
    if _engine is None:
        raise RuntimeError("Banco nao inicializado. Chame inicializar_banco() primeiro.")
    return _engine


def abrir_sessao():
    """Retorna uma sessao SQLAlchemy. Lembre de fechar com sessao.close()."""
    if _SessaoLocal is None:
        raise RuntimeError("Banco nao inicializado. Chame inicializar_banco() primeiro.")
    return _SessaoLocal()
