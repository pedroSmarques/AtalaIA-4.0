from sqlalchemy.orm import Session
from src.models import Usuario, CargoEnum, StatusContaEnum

# Valor especial: "nao mexer neste campo" (diferente de None, que limpa o campo)
_SEM_MUDANCA = object()


class UsuarioDAO:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, cpf: str, nome: str, email: str, senha_hash: str, cargo: CargoEnum, status_conta: StatusContaEnum) -> Usuario:
        novo_usuario = Usuario(
            cpf=cpf, nome=nome, email=email, 
            senha_hash=senha_hash, cargo=cargo, status_conta=status_conta
        )
        self.db.add(novo_usuario)
        self.db.commit()
        self.db.refresh(novo_usuario)
        return novo_usuario

    def buscar_por_id(self, id_usuario: int) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    
    def buscar_por_cpf(self, cpf: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.cpf == cpf).first()

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def listar_todos(self) -> list[Usuario]:
        return self.db.query(Usuario).all()

    def atualizar_perfil(self, id_usuario: int, nome: str | None = None, foto_perfil=_SEM_MUDANCA) -> Usuario | None:
        """Atualiza nome e/ou foto. foto_perfil=None remove a foto; omitido mantem a atual."""
        usuario = self.buscar_por_id(id_usuario)
        if not usuario:
            return None
        if nome is not None:
            usuario.nome = nome
        if foto_perfil is not _SEM_MUDANCA:
            usuario.foto_perfil = foto_perfil
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def atualizar(self, id_usuario: int, nome: str, email: str, cargo: CargoEnum, status_conta: StatusContaEnum) -> Usuario | None:
        usuario = self.buscar_por_id(id_usuario)
        if not usuario:
            return None
        usuario.nome, usuario.email = nome, email
        usuario.cargo, usuario.status_conta = cargo, status_conta
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def atualizar_senha(self, id_usuario: int, nova_senha_hash: str) -> bool:
        usuario = self.buscar_por_id(id_usuario)
        if not usuario:
            return False
        usuario.senha_hash = nova_senha_hash
        self.db.commit()
        return True

    def atualizar_status(self, id_usuario: int, novo_status: StatusContaEnum) -> Usuario | None:
        usuario = self.buscar_por_id(id_usuario)
        if usuario:
            usuario.status_conta = novo_status
            self.db.commit()
            self.db.refresh(usuario)
        return usuario

    def deletar(self, id_usuario: int) -> bool:
        usuario = self.buscar_por_id(id_usuario)
        if usuario:
            self.db.delete(usuario)
            self.db.commit()
            return True
        return False