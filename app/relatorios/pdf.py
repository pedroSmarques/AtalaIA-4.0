"""
Gera o PDF do relatorio com fpdf2 (no servidor).
Usa as fontes padrao do PDF (Helvetica): acentos do portugues funcionam; caracteres
fora do alfabeto latino (emoji, por exemplo) viram "?" para nao quebrar a geracao.
"""
import os
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import Align, TableBordersLayout, TableCellFillMode
from fpdf.fonts import FontFace

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGO = os.path.join(RAIZ, "static", "img", "logo-atalaia.svg")

# Paleta do sistema (a mesma do CSS), adaptada para papel
MARINHO = (14, 20, 38)
CIANO = (59, 180, 214)
LARANJA = (249, 115, 22)
TEXTO = (30, 40, 60)
SUAVE = (105, 116, 138)
LINHA = (214, 220, 232)
FUNDO_CARD = (243, 246, 251)


def _t(texto) -> str:
    """Texto seguro para fonte latina."""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


class RelatorioPDF(FPDF):
    def __init__(self, gerado_por: str, cargo: str, gerado_em: datetime):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.gerado_por = gerado_por
        self.cargo = cargo
        self.gerado_em = gerado_em
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)
        self.set_title("Relatorio ATALAIA")
        self.set_author("ATALAIA 4.0")
        self.set_creator("ATALAIA 4.0")
        self.alias_nb_pages()

    # ---- cabecalho (todas as paginas): logo + nome do sistema ----
    def header(self):
        self.set_fill_color(*MARINHO)
        self.rect(0, 0, 210, 22, style="F")
        self.set_fill_color(*CIANO)
        self.rect(0, 22, 210, 0.8, style="F")
        if os.path.exists(LOGO):
            self.image(LOGO, x=15, y=5, w=12, h=12)
        self.set_xy(31, 5.2)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(80, 6, "ATALAIA 4.0")
        self.set_xy(31, 11.2)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*CIANO)
        self.cell(80, 4, "SAFETY INTELLIGENCE")
        self.set_xy(120, 8.5)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(190, 200, 218)
        self.cell(75, 5, "Centro de Inteligência Operacional", align="R")
        self.set_y(30)

    # ---- rodape: quem gerou, quando e numero da pagina ----
    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*LINHA)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*SUAVE)
        quando = self.gerado_em.strftime("%d/%m/%Y %H:%M")
        self.cell(150, 5, _t(f"Gerado em {quando} por {self.gerado_por} ({self.cargo})"))
        self.cell(30, 5, f"Página {self.page_no()}/{{nb}}", align="R")


def _indicadores(pdf: RelatorioPDF, indicadores: list):
    """Cartoes de indicador, tres por linha."""
    largura, gap, altura = 57.3, 4.35, 19
    x0 = pdf.l_margin
    y = pdf.get_y()
    for i, (rotulo, valor) in enumerate(indicadores):
        coluna = i % 3
        if coluna == 0 and i > 0:
            y += altura + 4
        if coluna == 0 and y + altura > pdf.page_break_trigger:
            pdf.add_page()
            y = pdf.get_y()
        x = x0 + coluna * (largura + gap)
        pdf.set_fill_color(*FUNDO_CARD)
        pdf.set_draw_color(*LINHA)
        pdf.rect(x, y, largura, altura, style="DF")
        pdf.set_fill_color(*CIANO)
        pdf.rect(x, y, 1.2, altura, style="F")
        pdf.set_xy(x + 4, y + 3)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*SUAVE)
        pdf.cell(largura - 6, 4, _t(rotulo.upper()))
        pdf.set_xy(x + 4, y + 8.5)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*MARINHO)
        pdf.cell(largura - 6, 8, _t(valor))
    pdf.set_y(y + altura + 8)
    pdf.set_x(pdf.l_margin)


def _titulo_secao(pdf: RelatorioPDF, texto: str):
    if pdf.get_y() + 16 > pdf.page_break_trigger:
        pdf.add_page()
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*MARINHO)
    pdf.cell(0, 6, _t(texto.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*CIANO)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 18, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(3)


def gerar_pdf(dados: dict, pedido, gerado_por: str, cargo: str, gerado_em: datetime | None = None) -> bytes:
    """Monta o PDF e devolve os bytes."""
    gerado_em = gerado_em or datetime.now()
    pdf = RelatorioPDF(gerado_por, cargo, gerado_em)
    pdf.add_page()

    # titulo e periodo
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*LARANJA)
    pdf.cell(0, 5, "RELATÓRIO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*MARINHO)
    pdf.cell(0, 11, _t(dados["titulo"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*SUAVE)
    periodo = f"{pedido.inicio.strftime('%d/%m/%Y')} a {pedido.fim.strftime('%d/%m/%Y')}"
    pdf.cell(0, 6, _t(f"Período: {periodo}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # indicadores
    _titulo_secao(pdf, "Indicadores")
    _indicadores(pdf, dados["indicadores"])

    # tabela
    _titulo_secao(pdf, "Detalhamento")
    if dados["linhas"]:
        larguras = [c[1] for c in dados["colunas"]]
        alinhamentos = tuple(Align.R if c[2] == "R" else Align.L for c in dados["colunas"])
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TEXTO)
        pdf.set_draw_color(*LINHA)
        pdf.set_fill_color(*FUNDO_CARD)
        estilo_cab = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=MARINHO)
        with pdf.table(
            col_widths=tuple(larguras),
            text_align=alinhamentos,
            borders_layout=TableBordersLayout.HORIZONTAL_LINES,
            headings_style=estilo_cab,
            cell_fill_color=FUNDO_CARD,
            cell_fill_mode=TableCellFillMode.EVEN_ROWS,
            line_height=5.2,
            padding=1.6,
            repeat_headings=1,
        ) as tabela:
            cab = tabela.row()
            for coluna in dados["colunas"]:
                cab.cell(_t(coluna[0]))
            for n, linha in enumerate(dados["linhas"]):
                r = tabela.row()
                for valor in linha:
                    r.cell(_t(valor))
        pdf.ln(2)
        if dados.get("aviso"):
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*SUAVE)
            pdf.cell(0, 5, _t(dados["aviso"]), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*SUAVE)
        pdf.cell(0, 8, _t(dados["vazio"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # observacoes
    _titulo_secao(pdf, "Observações")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXTO)
    if pedido.observacoes:
        pdf.multi_cell(0, 5.5, _t(pedido.observacoes), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(*SUAVE)
        pdf.cell(0, 6, "Sem observações registradas.", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
