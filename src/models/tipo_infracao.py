import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class GravidadeEnum(str, enum.Enum):
    leve = "leve"
    media = "media"
    grave = "grave"
    critica = "critica"

class TipoInfracao(Base):
    __tablename__ = "TipoInfracao"

    id_tipo_infracao = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    gravidade = Column(Enum(GravidadeEnum), nullable=False)
    norma_relacionada = Column(String(30), nullable=True)

    # Relacionamentos
    incidentes = relationship("Incidente", back_populates="tipo_infracao")

    def __repr__(self):
        return f"<TipoInfracao(id={self.id_tipo_infracao}, nome='{self.nome}')>"