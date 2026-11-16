from sqlalchemy import Table, Column, Integer, ForeignKey
from src.database import Base

setor_usuario = Table(
    "setor_usuario",
    Base.metadata,
    Column("fk_Setor_id_setor", Integer, ForeignKey("Setor.id_setor", ondelete="CASCADE"), primary_key=True),
    Column("fk_Usuarios_id_usuario", Integer, ForeignKey("Usuarios.id_usuario", ondelete="CASCADE"), primary_key=True),
)
