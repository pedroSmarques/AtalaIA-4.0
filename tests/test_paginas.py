"""
Teste de fumaca: todas as telas de cada perfil abrem (200) COM dados no banco.
Pega erros que um banco vazio esconde (por exemplo, relacao lida depois de fechar a sessao).
"""
import pytest
from tests.conftest import entrar

PAGINAS = {
    "gestor_email": ["/gestor", "/gestor/alertas", "/gestor/alertas/1", "/gestor/cameras", "/gestor/usuarios",
                     "/gestor/setores", "/gestor/relatorios", "/gestor/logs", "/perfil"],
    "supervisor_email": ["/supervisor", "/supervisor/alertas", "/supervisor/alertas/1", "/supervisor/cameras",
                         "/supervisor/relatorio-ia", "/perfil"],
    "tecnico_email": ["/tecnico", "/tecnico/cameras", "/tecnico/logs", "/perfil"],
}


@pytest.mark.parametrize("perfil", list(PAGINAS))
def test_todas_as_telas_abrem_com_dados(app, usuarios_teste, dados_de_exemplo, perfil):
    with app.test_client() as c:
        entrar(c, usuarios_teste[perfil], usuarios_teste["senha"])
        for rota in PAGINAS[perfil]:
            r = c.get(rota)
            assert r.status_code == 200, f"{rota} devolveu {r.status_code}"
