from sqlalchemy.orm import Session
from src.models import Log

class LogDAO:
    def __init__(self, db: Session):
        self.db = db

    def registrar_log(self, acao: str, ip_origem: str, tabela: str = None, id_registro: int = None, detalhes: str = None, id_usuario: int = None) -> Log:
        novo_log = Log(
            acao_realizada=acao,
            tabela_afetada=tabela,
            id_registro_afetado=id_registro,
            ip_origem=ip_origem,
            detalhes=detalhes,
            fk_Usuarios_id_usuario=id_usuario
        )
        self.db.add(novo_log)
        self.db.commit()
        self.db.refresh(novo_log)
        return novo_log

    def listar_ultimos_logs(self, limite: int = 50) -> list[Log]:
        return self.db.query(Log).order_by(Log.data_hora.desc()).limit(limite).all()