# Autenticação — ATALAIA 4.0

**Autores originais:** ver `docs/arquivo/autenticacao-e-autorizacao.md`

---

## O que é autenticação

Responde: **"quem é você?"** — confirma a identidade antes de dar acesso.

## Fluxo de login

```
Navegador              Python (app.py)             Banco
──────────             ────────────────            ─────

1. POST /login ──────► lê e-mail, senha, cargo
                         │
                         ├──► DAO: busca usuário por e-mail
                         │◄── ficha ou None
                         │
                         ├─ usuário existe?        não ─► "credenciais inválidas"
                         ├─ bcrypt.check(senha)?   não ─►
                         ├─ cargo bate?            não ─►
                         │
                         └─ OK: session["id"] + session["cargo"]
                                     │
2. redirect ◄────────────────────────┘ → /supervisor | /gestor | /tecnico
```

## Campos usados

| Tabela `usuarios` | Uso |
|---|---|
| `email` | identifica o usuário |
| `senha_hash` | conferido com bcrypt (`checkpw`) — nunca compare texto puro |
| `cargo` | validado contra a aba selecionada na tela de login |
| `status_conta` | se `bloqueado` ou `inativo`, rejeitar mesmo com senha correta |
| `token_push` | gravado após permissão de notificação; não usado no login |

## Sessão (pulseira)

- Usar `session["id_usuario"]` e `session["cargo"]` após login bem-sucedido.
- `app.permanent_session_lifetime = timedelta(minutes=30)` — expira por inatividade.
- Logout: `session.clear()` + redirect `/`.

## Regras de segurança já definidas

- Senha armazenada **só** como hash bcrypt — nunca em texto puro.
- Mensagem de erro única: `"E-mail ou senha inválidos"` — não revelar qual campo falhou.
- O cargo na sessão vem do **banco**, não da aba da tela — a aba serve só para conferência.
- Após N tentativas erradas: bloquear temporariamente (ainda a implementar).

## Recuperação de senha

Fluxo ainda a definir pelo grupo. Sugestão: gerar token temporário (UUID), enviar por e-mail, invalidar após 15 min ou primeiro uso.
