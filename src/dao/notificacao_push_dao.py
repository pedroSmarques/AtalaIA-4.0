from sqlalchemy.orm import Session
from datetime import datetime
from src.models import NotificacaoPush, StatusEnvioEnum

class NotificacaoPushDAO:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, id_usuario: int, id_incidente: int, status_envio: StatusEnvioEnum) -> NotificacaoPush:
        nova_notificacao = NotificacaoPush(
            data_hora_envio=datetime.now(),
            status_envio=status_envio,
            fk_Usuarios_id_usuario=id_usuario,
            fk_Incidente_id_incidente=id_incidente
        )
        self.db.add(nova_notificacao)
        self.db.commit()
        self.db.refresh(nova_notificacao)
        return nova_notificacao

    def listar_por_usuario(self, id_usuario: int) -> list[NotificacaoPush]:
        return self.db.query(NotificacaoPush).filter(NotificacaoPush.fk_Usuarios_id_usuario == id_usuario).all()