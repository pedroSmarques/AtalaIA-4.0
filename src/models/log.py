from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Log(Base):
    __tablename__ = "logs"

    id_log = Column(Integer, primary_key=True, autoincrement=True)
    acao_realizada = Column(String(30), nullable=False)
    tabela_afetada = Column(String(50), nullable=True)
    id_registro_afetado = Column(Integer, nullable=True)
    ip_origem = Column(String(100), nullable=False)
    detalhes = Column(Text, nullable=True)
    data_hora = Column(DateTime, server_default=func.now())
    fk_Usuarios_id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=True)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="logs")

    def __repr__(self):
        return f"<Log(id={self.id_log}, acao='{self.acao_realizada}')>"