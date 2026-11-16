from sqlalchemy.orm import Session
from src.models import TipoInfracao, GravidadeEnum

class TipoInfracaoDAO:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, nome: str, gravidade: GravidadeEnum, norma_relacionada: str = None) -> TipoInfracao:
        nova_infracao = TipoInfracao(nome=nome, gravidade=gravidade, norma_relacionada=norma_relacionada)
        self.db.add(nova_infracao)
        self.db.commit()
        self.db.refresh(nova_infracao)
        return nova_infracao

    def buscar_por_id(self, id_tipo_infracao: int) -> TipoInfracao | None:
        return self.db.query(TipoInfracao).filter(TipoInfracao.id_tipo_infracao == id_tipo_infracao).first()

    def listar_todos(self) -> list[TipoInfracao]:
        return self.db.query(TipoInfracao).all()

    def deletar(self, id_tipo_infracao: int) -> bool:
        infracao = self.buscar_por_id(id_tipo_infracao)
        if infracao:
            self.db.delete(infracao)
            self.db.commit()
            return True
        return False