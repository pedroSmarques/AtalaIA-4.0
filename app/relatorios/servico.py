"""
Relatorios: quais tipos existem, quem pode gerar cada um, validacao do periodo
e coleta dos dados que vao para o PDF.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import joinedload

from src.models import Camera, Incidente, StatusAtendimentoEnum, StatusCameraEnum

# tipo -> rotulo, descricao e perfis que podem gerar (a permissao e checada no servidor)
TIPOS = {
    "incidentes": {
        "rotulo": "Relatório de Incidentes",
        "descricao": "Ocorrências detectadas pela IA no período.",
        "perfis": ("Gestor", "Supervisor"),
    },
    "cameras": {
        "rotulo": "Relatório de Câmeras",
        "descricao": "Disponibilidade e status das câmeras.",
        "perfis": ("Gestor", "Tecnico"),
    },
}

DIAS_PADRAO = 30
DIAS_MAXIMOS = 366
LIMITE_LINHAS = 1000
LIMITE_OBSERVACOES = 1000
_REGEX_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")


class ErroRelatorio(ValueError):
    """Erro de validacao com mensagem para o usuario e o campo afetado."""

    def __init__(self, mensagem: str, campo: str = ""):
        super().__init__(mensagem)
        self.campo = campo


def tipos_do_perfil(cargo: str) -> list[dict]:
    """Tipos de relatorio que o cargo informado pode gerar (para montar o modal)."""
    return [
        {"id": id_tipo, **dados}
        for id_tipo, dados in TIPOS.items()
        if cargo in dados["perfis"]
    ]


def periodo_padrao() -> tuple[str, str]:
    """Ultimos 30 dias, em ISO (valor inicial dos campos de data)."""
    hoje = date.today()
    return (hoje - timedelta(days=DIAS_PADRAO)).isoformat(), hoje.isoformat()


@dataclass
class Pedido:
    tipo: str
    inicio: date
    fim: date
    observacoes: str


def validar_pedido(form, cargo: str) -> Pedido:
    """Le e valida os campos do formulario. Levanta ErroRelatorio (400) ou PermissionError (403)."""
    tipo = (form.get("tipo") or "").strip()
    if tipo not in TIPOS:
        raise ErroRelatorio("Escolha um tipo de relatório.", "tipo")
    if cargo not in TIPOS[tipo]["perfis"]:
        raise PermissionError("Seu perfil não tem permissão para este relatório.")

    try:
        inicio = date.fromisoformat((form.get("inicio") or "").strip())
    except ValueError:
        raise ErroRelatorio("Informe a data inicial.", "inicio")
    try:
        fim = date.fromisoformat((form.get("fim") or "").strip())
    except ValueError:
        raise ErroRelatorio("Informe a data final.", "fim")
    if fim < inicio:
        raise ErroRelatorio("A data final deve ser igual ou depois da inicial.", "fim")
    if (fim - inicio).days > DIAS_MAXIMOS:
        raise ErroRelatorio("O período pode ter no máximo 1 ano.", "fim")

    observacoes = (form.get("observacoes") or "").strip()
    if len(observacoes) > LIMITE_OBSERVACOES:
        raise ErroRelatorio(f"Use no máximo {LIMITE_OBSERVACOES} caracteres nas observações.", "observacoes")

    return Pedido(tipo, inicio, fim, observacoes)


def validar_destinatario(texto: str) -> str:
    texto = (texto or "").strip()
    if not texto:
        raise ErroRelatorio("Informe o e-mail do destinatário.", "destinatario")
    if len(texto) > 254 or not _REGEX_EMAIL.match(texto):
        raise ErroRelatorio("Informe um e-mail válido, como nome@empresa.com.", "destinatario")
    return texto


def nome_do_arquivo(pedido: Pedido) -> str:
    return f"atalaia-relatorio-{pedido.tipo}-{pedido.inicio.isoformat()}_a_{pedido.fim.isoformat()}.pdf"


def _pct(valor: float) -> str:
    return f"{valor:.0f}%"


def coletar_dados(sessao, pedido: Pedido) -> dict:
    """
    Devolve tudo que o PDF precisa, ja em texto:
    {titulo, indicadores: [(rotulo, valor)], colunas: [(titulo, largura, alinhamento)], linhas, aviso}
    """
    de = datetime.combine(pedido.inicio, datetime.min.time())
    ate = datetime.combine(pedido.fim + timedelta(days=1), datetime.min.time())

    incidentes = (
        sessao.query(Incidente)
        .options(joinedload(Incidente.camera).joinedload(Camera.setor), joinedload(Incidente.tipo_infracao))
        .filter(Incidente.data_hora_deteccao >= de, Incidente.data_hora_deteccao < ate)
        .order_by(Incidente.data_hora_deteccao.desc())
        .all()
    )

    if pedido.tipo == "incidentes":
        return _dados_incidentes(incidentes)
    return _dados_cameras(sessao, incidentes)


def _dados_incidentes(incidentes: list) -> dict:
    total = len(incidentes)
    por_status = {s: 0 for s in StatusAtendimentoEnum}
    for i in incidentes:
        por_status[i.status_atendimento] += 1
    confianca = (sum(i.confianca_ia for i in incidentes) / total * 100) if total else 0

    indicadores = [
        ("Total de incidentes", str(total)),
        ("Pendentes", str(por_status[StatusAtendimentoEnum.pendente])),
        ("Em atendimento", str(por_status[StatusAtendimentoEnum.em_atendimento])),
        ("Resolvidos", str(por_status[StatusAtendimentoEnum.resolvido])),
        ("Falsos positivos", str(por_status[StatusAtendimentoEnum.falso_positivo])),
        ("Confiança média da IA", _pct(confianca) if total else "-"),
    ]
    colunas = [
        ("Registro", 17, "L"), ("Data e hora", 30, "L"), ("Infração", 46, "L"),
        ("Câmera / setor", 48, "L"), ("Conf.", 14, "R"), ("Status", 25, "L"),
    ]
    linhas = []
    for i in incidentes[:LIMITE_LINHAS]:
        cam = i.camera
        local = f"{cam.codigo_identificador} / {cam.setor.nome_setor}" if cam and cam.setor else "-"
        linhas.append([
            f"#A-{i.id_incidente}",
            i.data_hora_deteccao.strftime("%d/%m/%Y %H:%M"),
            i.tipo_infracao.nome if i.tipo_infracao else "-",
            local,
            _pct(i.confianca_ia * 100),
            i.status_atendimento.value.capitalize(),
        ])
    aviso = f"Exibindo os {LIMITE_LINHAS} incidentes mais recentes de {total}." if total > LIMITE_LINHAS else ""
    return {
        "titulo": "Relatório de Incidentes", "indicadores": indicadores,
        "colunas": colunas, "linhas": linhas, "aviso": aviso,
        "vazio": "Nenhum incidente registrado no período.",
    }


def _dados_cameras(sessao, incidentes: list) -> dict:
    cameras = sessao.query(Camera).options(joinedload(Camera.setor)).order_by(Camera.codigo_identificador).all()
    total = len(cameras)
    ativas = sum(1 for c in cameras if c.status == StatusCameraEnum.ativa)
    inativas = sum(1 for c in cameras if c.status == StatusCameraEnum.inativa)
    manutencao = total - ativas - inativas

    por_camera: dict[int, int] = {}
    for i in incidentes:
        por_camera[i.fk_Camera_id_camera] = por_camera.get(i.fk_Camera_id_camera, 0) + 1

    indicadores = [
        ("Câmeras cadastradas", str(total)),
        ("Ativas", str(ativas)),
        ("Inativas", str(inativas)),
        ("Em manutenção", str(manutencao)),
        ("Disponibilidade", _pct(ativas / total * 100) if total else "-"),
        ("Incidentes no período", str(len(incidentes))),
    ]
    colunas = [
        ("Código", 32, "L"), ("Setor", 60, "L"), ("Status", 38, "L"),
        ("FPS", 20, "R"), ("Incidentes", 30, "R"),
    ]
    linhas = [
        [
            c.codigo_identificador,
            c.setor.nome_setor if c.setor else "-",
            c.status.value.capitalize(),
            str(c.fps_operacao),
            str(por_camera.get(c.id_camera, 0)),
        ]
        for c in cameras[:LIMITE_LINHAS]
    ]
    return {
        "titulo": "Relatório de Câmeras", "indicadores": indicadores,
        "colunas": colunas, "linhas": linhas, "aviso": "",
        "vazio": "Nenhuma câmera cadastrada.",
    }
