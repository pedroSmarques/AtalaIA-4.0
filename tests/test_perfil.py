"""
Testes de "Meu perfil": foto (validacao pelo conteudo), nome, senha e isolamento entre usuarios.
"""
import io
import os
import re
import itertools

import bcrypt
import pytest
from PIL import Image

from src.database import abrir_sessao
from src.models import Usuario, CargoEnum, StatusContaEnum, Log
from tests.conftest import entrar

_contador = itertools.count(1)


@pytest.fixture
def pasta_avatares(app, tmp_path):
    """Grava as fotos de teste numa pasta temporaria."""
    anterior = app.config["PASTA_AVATARES"]
    app.config["PASTA_AVATARES"] = str(tmp_path / "avatares")
    yield tmp_path / "avatares"
    app.config["PASTA_AVATARES"] = anterior


@pytest.fixture
def criar_usuario(app):
    """Fabrica de usuarios novos (e-mail e CPF unicos), para um teste nao afetar outro."""
    def _criar(cargo=CargoEnum.Supervisor, nome="Maria da Silva"):
        n = next(_contador)
        sessao = abrir_sessao()
        try:
            u = Usuario(
                cpf=f"555.{n:03d}.000-00", nome=nome, email=f"perfil{n}@teste.com",
                senha_hash=bcrypt.hashpw(b"senha_teste_123", bcrypt.gensalt()).decode(),
                cargo=cargo, status_conta=StatusContaEnum.ativo,
            )
            sessao.add(u)
            sessao.commit()
            return {"id": u.id_usuario, "email": u.email}
        finally:
            sessao.close()
    return _criar


def _usuario(id_usuario):
    sessao = abrir_sessao()
    try:
        u = sessao.get(Usuario, id_usuario)
        sessao.expunge(u)
        return u
    finally:
        sessao.close()


def _imagem(formato="JPEG", tamanho=(800, 600), cor=(200, 60, 60)):
    buf = io.BytesIO()
    Image.new("RGB", tamanho, cor).save(buf, format=formato)
    buf.seek(0)
    return buf


def _enviar(cliente, arquivo, nome_arquivo, nome="Maria da Silva", extra=None):
    dados = {"nome": nome, "foto": (arquivo, nome_arquivo)}
    dados.update(extra or {})
    return cliente.post("/perfil/dados", data=dados, content_type="multipart/form-data")


# ------------------------------------------------------------------
# Foto
# ------------------------------------------------------------------

@pytest.mark.parametrize("formato,nome_arquivo", [("JPEG", "foto.jpg"), ("PNG", "foto.png"), ("WEBP", "foto.webp")])
def test_upload_valido_vira_webp_256_com_nome_aleatorio(app, criar_usuario, pasta_avatares, formato, nome_arquivo):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _enviar(c, _imagem(formato), nome_arquivo)
        assert r.status_code == 302

        foto = _usuario(u["id"]).foto_perfil
        assert re.fullmatch(r"[0-9a-f]{32}\.webp", foto)       # nome aleatorio, nunca o original
        caminho = pasta_avatares / foto
        assert caminho.exists()
        with Image.open(caminho) as img:
            assert img.format == "WEBP"
            assert img.size == (256, 256)

        # a foto aparece no topo da pagina
        pagina = c.get("/perfil").get_data(as_text=True)
        assert f"uploads/avatares/{foto}" in pagina


def test_foto_retangular_e_recortada_em_quadrado(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        _enviar(c, _imagem("JPEG", (1000, 300)), "larga.jpg")
        foto = _usuario(u["id"]).foto_perfil
        with Image.open(pasta_avatares / foto) as img:
            assert img.size == (256, 256)


def test_trocar_foto_apaga_a_antiga(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        _enviar(c, _imagem(), "a.jpg")
        primeira = _usuario(u["id"]).foto_perfil
        _enviar(c, _imagem(cor=(10, 200, 10)), "b.jpg")
        segunda = _usuario(u["id"]).foto_perfil
        assert primeira != segunda
        assert not (pasta_avatares / primeira).exists()
        assert (pasta_avatares / segunda).exists()


def test_arquivo_falso_renomeado_para_jpg_e_recusado(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        falso = io.BytesIO(b"MZ\x90\x00 isto e um executavel, nao uma imagem " * 50)
        r = _enviar(c, falso, "foto.jpg")
        assert r.status_code == 400
        assert "imagem válida" in r.get_data(as_text=True)
        assert _usuario(u["id"]).foto_perfil is None
        assert not pasta_avatares.exists() or not list(pasta_avatares.iterdir())


def test_script_html_com_extensao_de_imagem_e_recusado(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _enviar(c, io.BytesIO(b"<script>alert(1)</script>"), "foto.png")
        assert r.status_code == 400
        assert _usuario(u["id"]).foto_perfil is None


def test_formato_nao_permitido_mesmo_sendo_imagem_real(app, criar_usuario, pasta_avatares):
    """Um GIF e uma imagem de verdade, mas so JPG/PNG/WebP sao aceitos."""
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _enviar(c, _imagem("GIF"), "foto.png")
        assert r.status_code == 400
        assert _usuario(u["id"]).foto_perfil is None


def test_arquivo_maior_que_2mb_e_recusado(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    ruido = Image.frombytes("RGB", (900, 900), os.urandom(900 * 900 * 3))
    buf = io.BytesIO()
    ruido.save(buf, format="PNG")
    assert 2 * 1024 * 1024 < buf.tell() < 4 * 1024 * 1024
    buf.seek(0)
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _enviar(c, buf, "grande.png")
        assert r.status_code == 400
        assert "2 MB" in r.get_data(as_text=True)
        assert _usuario(u["id"]).foto_perfil is None


def test_corpo_gigante_e_barrado_antes_de_ler(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _enviar(c, io.BytesIO(b"\0" * (5 * 1024 * 1024)), "enorme.jpg")
        assert r.status_code in (302, 413)
        assert _usuario(u["id"]).foto_perfil is None


def test_remover_foto(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        _enviar(c, _imagem(), "a.jpg")
        foto = _usuario(u["id"]).foto_perfil
        r = c.post("/perfil/dados", data={"nome": "Maria da Silva", "remover_foto": "1"})
        assert r.status_code == 302
        assert _usuario(u["id"]).foto_perfil is None
        assert not (pasta_avatares / foto).exists()


def test_sem_foto_a_tela_mostra_iniciais(app, criar_usuario, pasta_avatares):
    u = criar_usuario(nome="Maria da Silva")
    with app.test_client() as c:
        entrar(c, u["email"])
        pagina = c.get("/perfil").get_data(as_text=True)
        assert 'class="av-ini">MD<' in pagina
        assert "av-img" not in pagina.split("<main")[0]   # nenhuma foto no cabecalho/menu


# ------------------------------------------------------------------
# Nome
# ------------------------------------------------------------------

def test_editar_nome(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = c.post("/perfil/dados", data={"nome": "  Maria   Souza  "})
        assert r.status_code == 302
        assert _usuario(u["id"]).nome == "Maria Souza"


def test_nome_vazio_e_recusado(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = c.post("/perfil/dados", data={"nome": "   "})
        assert r.status_code == 400
        assert _usuario(u["id"]).nome == "Maria da Silva"


# ------------------------------------------------------------------
# Isolamento: cada usuario altera so o proprio perfil
# ------------------------------------------------------------------

def test_usuario_nao_altera_perfil_de_outro(app, criar_usuario, pasta_avatares):
    atacante = criar_usuario(nome="Atacante")
    vitima = criar_usuario(nome="Vitima")
    with app.test_client() as c:
        entrar(c, atacante["email"])

        # tenta apontar o formulario para o id de outra pessoa
        r = c.post("/perfil/dados", data={"nome": "Hackeado", "id_usuario": str(vitima["id"])})
        assert r.status_code == 403
        r = _enviar(c, _imagem(), "x.jpg", nome="Hackeado", extra={"id_usuario": str(vitima["id"])})
        assert r.status_code == 403
        r = c.post("/perfil/senha", data={
            "id_usuario": str(vitima["id"]), "senha_atual": "senha_teste_123",
            "nova_senha": "NovaSenha@123", "confirmar_senha": "NovaSenha@123",
        })
        assert r.status_code == 403

    v = _usuario(vitima["id"])
    assert v.nome == "Vitima" and v.foto_perfil is None
    assert bcrypt.checkpw(b"senha_teste_123", v.senha_hash.encode())
    assert _usuario(atacante["id"]).nome == "Atacante"      # nada foi gravado em lugar nenhum


def test_alteracao_sem_login_vai_para_o_login(app):
    with app.test_client() as c:
        for rota in ("/perfil", "/perfil/dados", "/perfil/senha"):
            r = c.post(rota) if rota != "/perfil" else c.get(rota)
            assert r.status_code in (302, 405)
            if r.status_code == 302:
                assert "/login" in r.headers["Location"]


def test_o_formulario_nao_aceita_id_na_url(app, criar_usuario):
    """Nao existe rota /perfil/<id>: o alvo e sempre quem esta logado."""
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        assert c.post("/perfil/1/dados", data={"nome": "x"}).status_code == 404


# ------------------------------------------------------------------
# CSRF
# ------------------------------------------------------------------

def test_perfil_exige_csrf(app, criar_usuario, csrf_ligado, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = c.post("/perfil/dados", data={"nome": "Sem Token"})
        assert r.status_code == 403
        assert _usuario(u["id"]).nome == "Maria da Silva"

        token = c.get_cookie("csrf_access_token").value
        r = c.post("/perfil/dados", data={"nome": "Com Token", "csrf_token": token})
        assert r.status_code == 302
        assert _usuario(u["id"]).nome == "Com Token"


def test_formulario_da_tela_leva_o_token_csrf(app, criar_usuario, csrf_ligado):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        token = c.get_cookie("csrf_access_token").value
        pagina = c.get("/perfil").get_data(as_text=True)
        assert pagina.count(f'name="csrf_token" value="{token}"') >= 2   # dados, senha (e Sair)


# ------------------------------------------------------------------
# Senha
# ------------------------------------------------------------------

def _trocar_senha(c, atual, nova, confirma=None):
    return c.post("/perfil/senha", data={
        "senha_atual": atual, "nova_senha": nova, "confirmar_senha": nova if confirma is None else confirma,
    })


def test_trocar_senha_com_sucesso(app, criar_usuario):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _trocar_senha(c, "senha_teste_123", "OutraSenha@456")
        assert r.status_code == 302
    with app.test_client() as c2:
        assert c2.post("/login", data={"email": u["email"], "senha_hash": "senha_teste_123"}).status_code == 401
        assert c2.post("/login", data={"email": u["email"], "senha_hash": "OutraSenha@456"}).status_code == 302


def test_trocar_senha_pede_a_senha_atual(app, criar_usuario):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _trocar_senha(c, "errada", "OutraSenha@456")
        assert r.status_code == 400
        assert "senha atual não confere" in r.get_data(as_text=True)
        assert bcrypt.checkpw(b"senha_teste_123", _usuario(u["id"]).senha_hash.encode())


@pytest.mark.parametrize("nova,confirma,trecho", [
    ("curta", "curta", "pelo menos 8"),
    ("OutraSenha@456", "diferente@456", "confirmação"),
    ("senha_teste_123", "senha_teste_123", "diferente da atual"),
])
def test_senha_nova_invalida(app, criar_usuario, nova, confirma, trecho):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        r = _trocar_senha(c, "senha_teste_123", nova, confirma)
        assert r.status_code == 400
        assert trecho in r.get_data(as_text=True)
        assert bcrypt.checkpw(b"senha_teste_123", _usuario(u["id"]).senha_hash.encode())


# ------------------------------------------------------------------
# Acesso pelos tres perfis + registro nos logs
# ------------------------------------------------------------------

@pytest.mark.parametrize("cargo", [CargoEnum.Gestor, CargoEnum.Supervisor, CargoEnum.Tecnico])
def test_os_tres_perfis_abrem_meu_perfil_e_o_menu_aponta_para_ele(app, criar_usuario, cargo):
    u = criar_usuario(cargo=cargo)
    with app.test_client() as c:
        entrar(c, u["email"])
        r = c.get("/perfil")
        assert r.status_code == 200
        pagina = r.get_data(as_text=True)
        assert pagina.count('href="/perfil"') >= 3        # menu do avatar, menu lateral, painel "Mais"
        assert "Meu perfil" in pagina


def test_alteracoes_ficam_registradas_nos_logs(app, criar_usuario, pasta_avatares):
    u = criar_usuario()
    with app.test_client() as c:
        entrar(c, u["email"])
        _enviar(c, _imagem(), "a.jpg", nome="Maria Log")
        _trocar_senha(c, "senha_teste_123", "OutraSenha@456")
    sessao = abrir_sessao()
    try:
        acoes = {l.acao_realizada for l in sessao.query(Log).filter(Log.fk_Usuarios_id_usuario == u["id"])}
    finally:
        sessao.close()
    assert {"PERFIL_ATUALIZADO", "SENHA_ALTERADA"} <= acoes
