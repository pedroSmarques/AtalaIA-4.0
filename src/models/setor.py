import enum
from sqlalchemy import Column, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from src.models.associacoes import setor_usuario

class NivelRiscoEnum(str, enum.Enum):
    baixo = "baixo"
    medio = "medio"
    alto = "alto"
    critico = "critico"

class Setor(Base):
    __tablename__ = "Setor"

    id_setor = Column(Integer, primary_key=True, autoincrement=True)
    nome_setor = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=True)
    nivel_risco = Column(Enum(NivelRiscoEnum), nullable=False)

    # Relacionamentos
    usuarios = relationship("Usuario", secondary=setor_usuario, back_populates="setores")
    cameras = relationship("Camera", back_populates="setor")

    def __repr__(self):
        return f"<Setor(id={self.id_setor}, nome='{self.nome_setor}')>"
