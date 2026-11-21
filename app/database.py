# Re-exporta Base de src.database para manter compatibilidade com todos os models.
# Alguns models importam de app.database, outros de src.database — ambos apontam para a mesma Base.
from src.database import Base, inicializar_banco, abrir_sessao, obter_engine

__all__ = ["Base", "inicializar_banco", "abrir_sessao", "obter_engine"]
