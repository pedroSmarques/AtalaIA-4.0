from sqlalchemy.orm import Session
from datetime import datetime, date
from src.models import Incidente, StatusAtendimentoEnum

class IncidenteDAO:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, data_hora_deteccao: datetime, caminho_snapshot: str, confianca_ia: float, fk_Camera_id_camera: int, fk_TipoInfracao_id_tipo_infracao: int) -> Incidente:
        novo_incidente = Incidente(
            data_hora_deteccao=data_hora_deteccao,
            caminho_snapshot=caminho_snapshot,
            confianca_ia=confianca_ia,
            fk_Camera_id_camera=fk_Camera_id_camera,
            fk_TipoInfracao_id_tipo_infracao=fk_TipoInfracao_id_tipo_infracao
            # status_atendimento já começa como 'pendente' por padrão lá no Model
        )
        self.db.add(novo_incidente)
        self.db.commit()
        self.db.refresh(novo_incidente)
        return novo_incidente

    def buscar_por_id(self, id_incidente: int) -> Incidente | None:
        return self.db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()

    def listar_pendentes(self) -> list[Incidente]:
        return self.db.query(Incidente).filter(Incidente.status_atendimento == StatusAtendimentoEnum.pendente).all()

    def listar_todos(self) -> list[Incidente]:
        return self.db.query(Incidente).order_by(Incidente.data_hora_deteccao.desc()).all()

    def listar_por_status(self, status: StatusAtendimentoEnum) -> list[Incidente]:
        return self.db.query(Incidente).filter(Incidente.status_atendimento == status).all()

    def listar_recentes(self, limite: int = 5) -> list[Incidente]:
        return self.db.query(Incidente).order_by(Incidente.data_hora_deteccao.desc()).limit(limite).all()

    def contar_hoje(self) -> int:
        hoje = date.today()
        return self.db.query(Incidente).filter(
            Incidente.data_hora_deteccao >= datetime(hoje.year, hoje.month, hoje.day)
        ).count()

    def contar_resolvidos_hoje(self) -> int:
        hoje = date.today()
        return self.db.query(Incidente).filter(
            Incidente.status_atendimento == StatusAtendimentoEnum.resolvido,
            Incidente.data_hora_resolucao >= datetime(hoje.year, hoje.month, hoje.day),
        ).count()

    def atualizar_atendimento(self, id_incidente: int, status: StatusAtendimentoEnum, id_usuario: int, observacao: str = None) -> Incidente | None:
        incidente = self.buscar_por_id(id_incidente)
        if incidente:
            incidente.status_atendimento = status
            incidente.fk_Usuarios_id_usuario = id_usuario
            incidente.observacao_atendimento = observacao
            
            if status in [StatusAtendimentoEnum.resolvido, StatusAtendimentoEnum.falso_positivo]:
                incidente.data_hora_resolucao = datetime.now()

            self.db.commit()
            self.db.refresh(incidente)
        return incidente