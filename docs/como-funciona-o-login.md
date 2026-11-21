# Como funciona o login no ATALAIA 4.0

## O fluxo em palavras simples

Quando você entra no sistema, o servidor precisa responder duas perguntas:
1. **Quem é você?** — confirmado pela senha (autenticação)
2. **O que você pode ver?** — definido pelo seu cargo (autorização)

---

## Passo a passo: do clique ao dashboard

```mermaid
sequenceDiagram
    participant Navegador
    participant Flask
    participant Banco

    Navegador->>Flask: POST /login (e-mail + senha)
    Flask->>Banco: Busca usuario pelo e-mail
    Banco-->>Flask: Retorna ficha do usuario (ou vazio)
    Flask->>Flask: Confere a senha com bcrypt
    alt Credenciais corretas
        Flask->>Navegador: Salva dois cookies HttpOnly:<br/>access_token (15 min)<br/>refresh_token (7 dias)
        Navegador->>Flask: Redireciona para /gestor ou /supervisor ou /tecnico
    else Errado ou conta bloqueada
        Flask->>Navegador: "E-mail ou senha incorretos" (mesmo erro, sem revelar qual falhou)
    end

    Note over Navegador,Flask: Nas proximas requisicoes...

    Navegador->>Flask: GET /gestor (cookie enviado automaticamente)
    Flask->>Flask: Le o cookie, decodifica o JWT
    Flask->>Flask: Verifica: token valido? cargo = Gestor?
    alt Tudo certo
        Flask->>Navegador: Renderiza o dashboard
    else Token expirado
        Flask->>Flask: Tenta renovar com o refresh token
        Flask->>Navegador: Novo access token no cookie + pagina carregada
    else Cargo errado
        Flask->>Navegador: HTTP 403 — Acesso negado
    end
```

---

## O que é o JWT (a "pulseira de entrada")

Pense no JWT como uma pulseira de show: ela prova que você pagou o ingresso e diz qual área você pode entrar. O servidor não precisa consultar o banco a cada clique — ele só lê a pulseira.

- **access_token** — válido por 15 minutos; enviado em todo pedido
- **refresh_token** — válido por 7 dias; usado só para gerar um novo access_token quando ele expira
- Ambos ficam em **cookies HttpOnly**: o JavaScript da página não consegue lê-los, o que protege contra ataques XSS

---

## Por que dois tokens?

| Token | Duração | Para que serve |
|---|---|---|
| access_token | 15 min | Autoriza cada requisição |
| refresh_token | 7 dias | Renova o access_token sem pedir login |

Se o access_token for roubado, ele expira em 15 minutos. O refresh_token nunca sai do cookie seguro.

---

## Proteção CSRF

Sem proteção, uma página maliciosa poderia fazer seu navegador enviar requisições ao ATALAIA sem você saber. Para evitar isso, usamos o método **double-submit**:

1. O servidor grava um token CSRF num cookie que o JavaScript **pode** ler
2. Todo formulário POST inclui esse token num campo oculto
3. O servidor confere: o token do cookie bate com o do formulário? Se não, rejeita

---

## O que fica gravado no JWT

Apenas o ID do usuário e o cargo — nenhum dado sensível como CPF ou e-mail.

```json
{
  "sub": "42",
  "cargo": "Supervisor",
  "exp": 1748000000
}
```
