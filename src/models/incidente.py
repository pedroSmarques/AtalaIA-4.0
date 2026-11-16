import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class StatusAtendimentoEnum(str, enum.Enum):
    pendente = "pendente"
    em_atendimento = "em atendimento"
    resolvido = "resolvido"
    falso_positivo = "falso positivo"

class Incidente(Base):
    __tablename__ = "Incidente"

    id_incidente = Column(Integer, primary_key=True, autoincrement=True)
    data_hora_deteccao = Column(DateTime, nullable=False)
    caminho_snapshot = Column(String(255), nullable=False)
    confianca_ia = Column(Float, nullable=False)
    status_atendimento = Column(
        Enum(StatusAtendimentoEnum, values_callable=lambda obj: [e.value for e in obj]),
        default=StatusAtendimentoEnum.pendente,
        nullable=False
    )
    observacao_atendimento = Column(Text, nullable=True)
    data_hora_resolucao = Column(DateTime, nullable=True)

    fk_Camera_id_camera = Column(Integer, ForeignKey("Camera.id_camera"), nullable=False)
    fk_TipoInfracao_id_tipo_infracao = Column(Integer, ForeignKey("TipoInfracao.id_tipo_infracao"), nullable=False)
    fk_Usuarios_id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=True)

    # Relacionamentos
    camera = relationship("Camera", back_populates="incidentes")
    tipo_infracao = relationship("TipoInfracao", back_populates="incidentes")
    responsavel = relationship("Usuario", back_populates="incidentes_atendidos")
    notificacoes = relationship("NotificacaoPush", back_populates="incidente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Incidente(id={self.id_incidente}, status='{self.status_atendimento.value}')>"