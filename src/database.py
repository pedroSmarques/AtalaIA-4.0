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


# Colunas adicionadas depois da primeira versao do banco: (tabela, coluna, definicao SQL)
_COLUNAS_NOVAS = [
    ("Usuarios", "foto_perfil", "VARCHAR(100) NULL"),
]


def garantir_colunas_novas():
    """
    Adiciona ao banco ja existente as colunas criadas depois da primeira versao.
    Idempotente: se a coluna ja existe (ou a tabela ainda nao existe), nao faz nada.
    O create_all() do SQLAlchemy cria tabelas novas, mas nao altera tabelas existentes.
    """
    from sqlalchemy import inspect, text
    engine = obter_engine()
    inspetor = inspect(engine)
    for tabela, coluna, definicao in _COLUNAS_NOVAS:
        nome_real = next((t for t in inspetor.get_table_names() if t.lower() == tabela.lower()), None)
        if nome_real is None:
            continue
        existentes = {c["name"].lower() for c in inspetor.get_columns(nome_real)}
        if coluna.lower() in existentes:
            continue
        with engine.begin() as conexao:
            conexao.execute(text(f"ALTER TABLE {nome_real} ADD COLUMN {coluna} {definicao}"))
