import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class StatusCameraEnum(str, enum.Enum):
    ativa = "ativa"
    inativa = "inativa"
    manutencao = "manutenção"

class Camera(Base):
    __tablename__ = "Camera"

    id_camera = Column(Integer, primary_key=True, autoincrement=True)
    codigo_identificador = Column(String(50), nullable=False)
    url_rtsp_stream = Column(String(512), nullable=False)
    status = Column(
        Enum(StatusCameraEnum, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    fps_operacao = Column(Integer, nullable=False)
    fk_Setor_id_setor = Column(Integer, ForeignKey("Setor.id_setor"), nullable=False)

    # Relacionamentos
    setor = relationship("Setor", back_populates="cameras")
    incidentes = relationship("Incidente", back_populates="camera")

    def __repr__(self):
        return f"<Camera(id={self.id_camera}, codigo='{self.codigo_identificador}')>"
