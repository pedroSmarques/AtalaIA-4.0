import enum
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class StatusEnvioEnum(str, enum.Enum):
    enviado = "enviado"
    entregue = "entregue"
    lido = "lido"
    falha = "falha"

class NotificacaoPush(Base):
    __tablename__ = "notificacoesPush"

    id_notificacao = Column(Integer, primary_key=True, autoincrement=True)
    data_hora_envio = Column(DateTime, nullable=False)
    status_envio = Column(Enum(StatusEnvioEnum), nullable=False)
    fk_Usuarios_id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    fk_Incidente_id_incidente = Column(Integer, ForeignKey("Incidente.id_incidente", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="notificacoes")
    incidente = relationship("Incidente", back_populates="notificacoes")

    def __repr__(self):
        return f"<NotificacaoPush(id={self.id_notificacao}, status='{self.status_envio.value}')>"
