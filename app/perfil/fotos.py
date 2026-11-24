"""
Foto de perfil: valida pelo CONTEUDO (Pillow), recorta em quadrado e regrava em WebP.
Nunca confia na extensao nem no Content-Type enviados pelo navegador.
"""
import io
import os
import secrets
from PIL import Image, ImageOps, UnidentifiedImageError

TAMANHO_MAXIMO = 2 * 1024 * 1024        # 2 MB
LADO = 256                              # px (quadrado)
FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP"}
PIXELS_MAXIMOS = 40_000_000             # protege contra "bomba de descompressao"


class ErroFoto(ValueError):
    """Mensagem pronta para mostrar ao usuario."""


def processar_foto(arquivo) -> bytes:
    """Recebe o FileStorage do formulario e devolve os bytes do WebP 256x256."""
    dados = arquivo.stream.read(TAMANHO_MAXIMO + 1)
    if not dados:
        raise ErroFoto("Escolha uma imagem.")
    if len(dados) > TAMANHO_MAXIMO:
        raise ErroFoto("A foto deve ter no máximo 2 MB.")

    mensagem = "Envie uma imagem válida em JPG, PNG ou WebP."
    try:
        imagem = Image.open(io.BytesIO(dados))
        if imagem.format not in FORMATOS_ACEITOS:
            raise ErroFoto(mensagem)
        if imagem.width * imagem.height > PIXELS_MAXIMOS:
            raise ErroFoto("A imagem tem dimensões grandes demais.")
        imagem.verify()                         # checa a estrutura do arquivo
        imagem = Image.open(io.BytesIO(dados))  # verify() invalida o objeto: reabre
        imagem.load()                           # decodifica de verdade (acusa arquivo corrompido)
    except ErroFoto:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ErroFoto(mensagem)

    imagem = ImageOps.exif_transpose(imagem)    # respeita a rotacao de fotos de celular
    tem_transparencia = imagem.mode in ("RGBA", "LA") or "transparency" in imagem.info
    imagem = imagem.convert("RGBA" if tem_transparencia else "RGB")
    imagem = ImageOps.fit(imagem, (LADO, LADO), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    saida = io.BytesIO()
    imagem.save(saida, format="WEBP", quality=85, method=4)   # sem EXIF/metadados
    return saida.getvalue()


def salvar_foto(arquivo, pasta: str) -> str:
    """Valida, converte e grava com nome aleatorio. Devolve o nome do arquivo."""
    conteudo = processar_foto(arquivo)
    os.makedirs(pasta, exist_ok=True)
    nome = f"{secrets.token_hex(16)}.webp"
    with open(os.path.join(pasta, nome), "wb") as f:
        f.write(conteudo)
    return nome


def apagar_foto(pasta: str, nome: str | None) -> None:
    """Remove a foto antiga (ignora se nao existir). So aceita nomes simples gerados por nos."""
    if not nome or os.path.basename(nome) != nome or not nome.endswith(".webp"):
        return
    try:
        os.remove(os.path.join(pasta, nome))
    except OSError:
        pass
