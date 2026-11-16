# Autorização — ATALAIA 4.0

**Autores originais:** ver `docs/arquivo/autenticacao-e-autorizacao.md`

---

## O que é autorização

Responde: **"o que você pode fazer?"** — aplicada depois que a identidade já foi confirmada.

## Como funciona no Flask

```python
@app.route("/gestor")
@login_obrigatorio      # catraca 1: tem sessão?
@so_perfil("Gestor")    # catraca 2: cargo correto?
def painel_gestor():
    ...
```

O decorador `@so_perfil` lê `session["cargo"]` — que vem do banco, não da tela.

## Tabela de permissões por tela/ação

| Tela / Ação | Gestor | Supervisor | Técnico |
|---|:---:|:---:|:---:|
| **Login / logout** | ✅ | ✅ | ✅ |
| **Dashboard** (visão geral) | ✅ | ✅ | ✅ |
| **Alertas** — visualizar lista | ✅ | ✅ | — |
| **Alertas** — atualizar status | ✅ | ✅ | — |
| **Alertas** — detalhe + snapshot | ✅ | ✅ | — |
| **Câmeras** — visualizar lista | ✅ | ✅ (leitura) | ✅ |
| **Câmeras** — criar / excluir | ✅ | — | — |
| **Câmeras** — editar URL/FPS/status | ✅ | — | ✅ |
| **Usuários** — visualizar | ✅ | — | — |
| **Usuários** — criar / editar / bloquear | ✅ | — | — |
| **Setores** — visualizar | ✅ | — | — |
| **Setores** — criar / editar | ✅ | — | — |
| **Relatórios** | ✅ | ✅ (Relatório IA) | — |
| **Logs do sistema** | ✅ | — | ✅ |
| **Notificações push** — receber | ✅ | ✅ | ✅ |

## Comportamento para acesso negado

- Rota sem sessão → redirect `/` (tela de login).
- Rota com sessão mas cargo errado → HTTP 403 `"Acesso negado"`.
- O JS pode ocultar botões e menus, mas a **verificação real é sempre no servidor**.

## Cargos no modelo

```python
class CargoEnum(str, enum.Enum):
    Gestor     = "Gestor"
    Supervisor = "Supervisor"
    Tecnico    = "Tecnico"
```

Use exatamente esses valores nas chamadas a `@so_perfil()`.
