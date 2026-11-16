import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.associacoes import setor_usuario

class CargoEnum(str, enum.Enum):
    Gestor = "Gestor"
    Supervisor = "Supervisor"
    Tecnico = "Tecnico"

class StatusContaEnum(str, enum.Enum):
    ativo = "ativo"
    inativo = "inativo"
    bloqueado = "bloqueado"

class Usuario(Base):
    __tablename__ = "Usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(14), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cargo = Column(Enum(CargoEnum), nullable=False)
    status_conta = Column(Enum(StatusContaEnum), nullable=False)
    token_push = Column(String(255), nullable=True)
    data_criacao = Column(DateTime, server_default=func.now())

    # Relacionamentos
    setores = relationship("Setor", secondary=setor_usuario, back_populates="usuarios")
    incidentes_atendidos = relationship("Incidente", back_populates="responsavel")
    notificacoes = relationship("NotificacaoPush", back_populates="usuario")
    logs = relationship("Log", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(id={self.id_usuario}, nome='{self.nome}', cargo='{self.cargo.value}')>"