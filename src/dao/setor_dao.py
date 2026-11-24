from sqlalchemy.orm import Session
from src.models import Setor, NivelRiscoEnum

class SetorDAO:
    def __init__(self, db: Session):
        self.db = db

    def listar_todos(self) -> list[Setor]:
        return self.db.query(Setor).all()

    def buscar_por_id(self, id_setor: int) -> Setor | None:
        return self.db.query(Setor).filter(Setor.id_setor == id_setor).first()

    def atualizar(self, id_setor: int, nome_setor: str, nivel_risco: NivelRiscoEnum, descricao: str = None) -> Setor | None:
        setor = self.buscar_por_id(id_setor)
        if not setor:
            return None
        setor.nome_setor, setor.nivel_risco, setor.descricao = nome_setor, nivel_risco, descricao
        self.db.commit()
        self.db.refresh(setor)
        return setor

    def criar(self, nome_setor: str, nivel_risco: NivelRiscoEnum, descricao: str = None) -> Setor:
        novo = Setor(nome_setor=nome_setor, nivel_risco=nivel_risco, descricao=descricao)
        self.db.add(novo)
        self.db.commit()
        self.db.refresh(novo)
        return novo
