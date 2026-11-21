from sqlalchemy.orm import Session
from src.models import Camera, StatusCameraEnum

class CameraDAO:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, codigo_identificador: str, url_rtsp_stream: str, status: StatusCameraEnum, fps_operacao: int, fk_Setor_id_setor: int) -> Camera:
        nova_camera = Camera(
            codigo_identificador=codigo_identificador,
            url_rtsp_stream=url_rtsp_stream,
            status=status,
            fps_operacao=fps_operacao,
            fk_Setor_id_setor=fk_Setor_id_setor
        )
        self.db.add(nova_camera)
        self.db.commit()
        self.db.refresh(nova_camera)
        return nova_camera

    def buscar_por_id(self, id_camera: int) -> Camera | None:
        return self.db.query(Camera).filter(Camera.id_camera == id_camera).first()

    def listar_todas(self) -> list[Camera]:
        return self.db.query(Camera).all()

    def listar_por_setor(self, id_setor: int) -> list[Camera]:
        return self.db.query(Camera).filter(Camera.fk_Setor_id_setor == id_setor).all()

    def atualizar_status(self, id_camera: int, novo_status: StatusCameraEnum) -> Camera | None:
        camera = self.buscar_por_id(id_camera)
        if camera:
            camera.status = novo_status
            self.db.commit()
            self.db.refresh(camera)
        return camera

    def deletar(self, id_camera: int) -> bool:
        camera = self.buscar_por_id(id_camera)
        if camera:
            self.db.delete(camera)
            self.db.commit()
            return True
        return False