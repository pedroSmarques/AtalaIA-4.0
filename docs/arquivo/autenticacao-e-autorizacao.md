# 🔐 Autenticação e Autorização — ATALAIA 4.0

> Documento da parte de **segurança e login** do sistema.
> Feito para estudo e para o grupo todo entender, sem precisar ser expert.

**Responsável pela parte:** ______________________
**Local deste arquivo:** `AtalaIA-4.0/DOCS/autenticacao-e-autorizacao.md`

---

## 📌 Índice

1. [A ideia em uma frase](#1-a-ideia-em-uma-frase)
2. [A analogia geral: o prédio da empresa](#2-a-analogia-geral-o-prédio-da-empresa)
3. [Dicionário rápido](#3-dicionário-rápido)
4. [Onde fica cada arquivo](#4-onde-fica-cada-arquivo)
5. [O caminho do login (diagrama)](#5-o-caminho-do-login-diagrama)
6. [Passo a passo com código comentado](#6-passo-a-passo-com-código-comentado)
7. [Como testar](#7-como-testar)
8. [Regras de segurança](#8-regras-de-segurança)
9. [Erros comuns](#9-erros-comuns)
10. [Próximos passos](#10-próximos-passos)

---

## 1. A ideia em uma frase

A pessoa digita e-mail e senha, o Python confere no banco se ela existe e se a senha está certa, e então **manda ela direto pro painel do seu perfil** (Supervisor, Gestor ou Técnico TI). Quem tentar entrar sem login, ou tentar abrir o painel de outro perfil, é barrado.

Duas palavras que parecem iguais mas **não são**:

| Palavra | Pergunta que responde | Exemplo do dia a dia |
|---|---|---|
| **Autenticação** | "Quem é você?" | Mostrar o RG na portaria |
| **Autorização** | "O que você pode fazer aqui?" | O crachá só abre as portas do seu andar |

---

## 2. A analogia geral: o prédio da empresa

Imagine que o ATALAIA é um **prédio de uma empresa**. Cada peça do nosso código tem um papel nesse prédio:

| Peça do código | Quem é no prédio | O que faz |
|---|---|---|
| `index.html` (tela de login) | 🚪 A **porta de entrada** | É por onde a pessoa chega e se apresenta |
| `app.py` | 🧑‍💼 O **recepcionista** | Recebe a pessoa, chama os outros e decide pra onde ela vai |
| `dao/usuario_dao.py` | 🗂️ O **arquivista** | Vai no arquivo e traz a ficha do funcionário |
| `factory/conexao.py` | ☎️ A **linha direta** com o arquivo | É o telefone que liga pro banco de dados |
| Banco de dados (tabela `usuarios`) | 🏢 O **arquivo central** | Onde ficam todas as fichas guardadas |
| `models/seguranca.py` | 💂 O **segurança / catraca** | Confere a senha e barra quem não pode passar |
| `session` (sessão) | 🎟️ A **pulseira do evento** | Depois do login, a pessoa ganha uma pulseira e não precisa se identificar de novo a cada sala |
| `perfil` (supervisor/gestor/ti) | 🎨 A **cor do crachá** | Define em quais andares a pessoa entra |
| Painéis (`supervisor/`, `dashboard_gestor/`) | 🏬 Os **andares** | Cada perfil tem o seu |

> 💡 **Resumindo a história:** a pessoa chega na porta (HTML), fala com o recepcionista (`app.py`), que pede pro arquivista (DAO) buscar a ficha no arquivo (banco). O segurança (`seguranca.py`) confere se a senha bate. Se sim, entrega a pulseira (session) e o recepcionista leva a pessoa pro andar certo.

---

## 3. Dicionário rápido

| Termo | Explicação simples | Analogia |
|---|---|---|
| **Flask** | Ferramenta que transforma o Python num "servidor" que atende o navegador | O prédio em si, com recepção funcionando |
| **Rota** (`@app.route`) | Um endereço do site e o que o Python faz quando alguém acessa | Placa na porta: "Sala 3 → faça isso" |
| **Formulário (`<form>`)** | A parte do HTML que envia dados pro Python | Preencher uma ficha de visitante |
| **DAO** | Arquivo que só conversa com o banco | O arquivista |
| **Hash de senha** | Senha transformada em um "embaralhado" que **não tem volta** | Um bolo: dá pra fazer o bolo seguindo a receita, mas não dá pra desfazer o bolo e recuperar os ovos |
| **bcrypt** | A ferramenta que faz o hash de forma segura | O forno especial da cozinha |
| **Sessão (`session`)** | Memória do servidor sobre quem já fez login | A pulseira do evento |
| **Decorador (`@login_obrigatorio`)** | Uma linha colocada acima de uma função pra ela ganhar uma regra | A catraca instalada na frente de uma sala |
| **SQL Injection** | Ataque onde alguém escreve código malicioso no campo de texto | Alguém escreve "e abra o cofre" na ficha de visitante e o arquivista obedece |
| **Perfil** | O tipo de usuário (supervisor, gestor, ti) | A cor do crachá |

---

## 4. Onde fica cada arquivo

Mantendo exatamente a divisão de pastas que o grupo já criou:

```
AtalaIA-4.0/
├── DOCS/                              ← NOVA: documentação (este arquivo mora aqui)
│   └── autenticacao-e-autorizacao.md
├── requirements.txt                   ← lista das ferramentas que o projeto usa
└── src/
    ├── app.py                         ← NOVO: o recepcionista (liga tudo)
    ├── factory/
    │   └── conexao.py                 ← NOVO: a linha direta com o banco
    ├── dao/
    │   └── usuario_dao.py             ← NOVO: o arquivista
    ├── models/
    │   └── seguranca.py               ← NOVO: o segurança / catraca
    ├── migrations/
    │   ├── 001_criar_tabela_usuarios.sql      ← NOVO: cria a tabela
    │   └── criar_usuario_inicial.py           ← NOVO: cadastra o 1º usuário
    └── views/
        ├── index.html                 ← JÁ EXISTE: tela de login (vamos ajustar)
        ├── paginaLogin.css            ← JÁ EXISTE
        ├── img/
        ├── supervisor/                ← painel do supervisor (outro integrante)
        └── dashboard_gestor/          ← painel do gestor (outro integrante)
```

---

## 5. O caminho do login (diagrama)

```
 NAVEGADOR (HTML)                 PYTHON (app.py)                    BANCO
 ────────────────                 ───────────────                    ─────

 1. abre o site  ───────────────► rota "/" entrega o index.html
                 ◄───────────────  (tela de login aparece)

 2. escolhe a aba (Supervisor,
    Gestor ou Técnico TI),
    digita e-mail e senha,
    clica em "Entrar" ──────────► rota "/login" recebe os 3 dados
                                   │
                                   ├─► DAO: "traga a ficha deste e-mail" ──► tabela usuarios
                                   │◄───────── ficha (ou nada) ◄───────────┘
                                   │
                                   ├─ achou o usuário?          ── não ──┐
                                   ├─ a senha confere (hash)?   ── não ──┤
                                   ├─ o perfil da aba é o dele? ── não ──┤
                                   │                                     ▼
 3a. ERRO ◄────────────────────────┴──────────────── "E-mail ou senha inválidos"
                                   │
                                   └─ tudo certo → guarda na sessão (pulseira)
                                                   e olha o perfil:
                                         │
 3b. painel certo ◄──────────────────────┼─ supervisor → /supervisor
                                         ├─ gestor     → /gestor
                                         └─ ti         → /ti
```

**E quando alguém tenta entrar direto numa página protegida?**

```
 Alguém digita /gestor na barra do navegador
        │
        ▼
 Catraca 1: tem pulseira (sessão)?  ── não ──► volta pro login
        │ sim
        ▼
 Catraca 2: a cor do crachá (perfil) é "gestor"? ── não ──► "Acesso negado"
        │ sim
        ▼
 Painel do gestor abre ✅
```

---

## 6. Passo a passo com código comentado

> 📖 Em cada código, **todas as linhas têm um comentário** (o texto depois do `#`, ou entre `<!-- -->` no HTML). Leia os comentários como se fossem a narração do que está acontecendo.

### Passo 1 — Criar a pasta DOCS

Na raiz do projeto (do lado de `src`), crie a pasta `DOCS` e coloque este arquivo nela.

### Passo 2 — Instalar as ferramentas

No terminal:

```bash
pip install flask bcrypt mysql-connector-python
```

E deixe anotado no `requirements.txt` (assim qualquer pessoa do grupo instala tudo de uma vez com `pip install -r requirements.txt`):

```
flask
bcrypt
mysql-connector-python
```

| Ferramenta | Pra que serve | Analogia |
|---|---|---|
| `flask` | Faz o Python atender o navegador | O prédio com recepção |
| `bcrypt` | Embaralha e confere senhas com segurança | O forno que faz o "bolo" da senha |
| `mysql-connector-python` | Deixa o Python conversar com o MySQL | O cabo de telefone até o arquivo |

> ⚠️ Se o grupo usar outro banco (PostgreSQL, SQLite...), só muda a ferramenta e o arquivo `conexao.py`. O resto fica igual.

---

### Passo 3 — Criar a tabela de usuários

**Arquivo:** `src/migrations/001_criar_tabela_usuarios.sql`

> 🗂️ **Analogia:** é montar o **gaveteiro** onde as fichas dos funcionários vão ficar.
> Se o grupo já tem uma tabela de usuários, não crie outra: ajuste os nomes das colunas no código.

```sql
CREATE TABLE IF NOT EXISTS usuarios (            -- cria o gaveteiro "usuarios" (só se ainda não existir)
    id INT AUTO_INCREMENT PRIMARY KEY,           -- número da ficha, sobe sozinho: 1, 2, 3...
    nome VARCHAR(100) NOT NULL,                  -- nome da pessoa (obrigatório, até 100 letras)
    email VARCHAR(150) NOT NULL UNIQUE,          -- e-mail (obrigatório e NÃO pode repetir)
    senha_hash VARCHAR(100) NOT NULL,            -- a senha EMBARALHADA (nunca a senha de verdade!)
    perfil ENUM('supervisor','gestor','ti')      -- a "cor do crachá": só aceita um destes 3 valores
        NOT NULL,                                -- e é obrigatório
    ativo TINYINT(1) NOT NULL DEFAULT 1          -- 1 = pode entrar, 0 = bloqueado (ex.: saiu da empresa)
);
```

> 🔑 **Regra de ouro:** a coluna se chama `senha_hash` justamente pra lembrar que **nunca** guardamos a senha de verdade. Se o banco vazar, ninguém consegue ler as senhas.

---

### Passo 4 — A linha direta com o banco

**Arquivo:** `src/factory/conexao.py`

> ☎️ **Analogia:** é o **telefone** que liga pro arquivo central. Qualquer um que precisar do banco liga por aqui, assim a senha do banco fica em **um lugar só**.

```python
import mysql.connector  # traz a ferramenta que sabe conversar com o MySQL (como instalar o app do telefone)

def conectar():  # cria a função "conectar": quem precisar do banco é só chamar ela
    return mysql.connector.connect(  # devolve uma conexão aberta (o telefone já discando pro banco)
        host="localhost",  # onde o banco mora; "localhost" = neste mesmo computador
        user="root",  # usuário DO BANCO (não confundir com o usuário do sistema)
        password="sua_senha",  # senha DO BANCO (troque pela sua)
        database="atalaia"  # qual banco abrir dentro do MySQL (qual gaveteiro)
    )  # fecha a lista de configurações
```

> ⚠️ **Cuidado:** não suba a senha real do banco no Git. Se o repositório for compartilhado, use uma variável de ambiente ou um arquivo `.env` que esteja no `.gitignore`.

---

### Passo 5 — O arquivista (DAO)

**Arquivo:** `src/dao/usuario_dao.py`

> 🗂️ **Analogia:** o DAO é o **arquivista**. Ele não decide nada, não confere senha, não liga pra regra. Só faz **uma coisa**: recebe um e-mail, vai no arquivo e traz a ficha. Se não achar, volta de mãos vazias (`None`).

```python
from factory.conexao import conectar  # pega a função "conectar" do arquivo conexao.py (pede o telefone emprestado)

def buscar_por_email(email):  # função do arquivista: recebe um e-mail e procura a ficha dessa pessoa
    con = conectar()  # liga pro banco; "con" guarda a ligação
    cur = con.cursor(dictionary=True)  # cursor = a "caneta" que faz perguntas e lê respostas; dictionary=True faz a resposta vir com nomes (usuario["perfil"]) em vez de posições (usuario[4])
    cur.execute(  # manda a pergunta (em SQL) pro banco
        "SELECT id, nome, email, senha_hash, perfil "  # "traga estes campos..."
        "FROM usuarios "  # "...da tabela usuarios..."
        "WHERE email = %s AND ativo = 1",  # "...onde o e-mail seja o informado E a pessoa esteja ativa"; %s é um espaço reservado SEGURO
        (email,)  # o valor que entra no lugar do %s (a vírgula é obrigatória, cria uma "tupla" de 1 item)
    )  # fim da pergunta
    usuario = cur.fetchone()  # pega UMA linha da resposta; se ninguém foi encontrado, vem None (nada)
    cur.close()  # larga a caneta
    con.close()  # desliga o telefone (sempre feche, senão a linha fica ocupada)
    return usuario  # devolve a ficha (ou None) pra quem pediu
```

> 🛡️ **Por que o `%s` e não juntar o texto direto?**
> Se a gente escrevesse `"... WHERE email = '" + email + "'"`, um invasor poderia digitar no campo de e-mail algo como `' OR '1'='1` e **enganar o arquivista**, entrando sem senha. Com o `%s`, o banco trata tudo que o usuário digitou como **simples texto**, nunca como ordem. É a diferença entre o arquivista **ler** o que está escrito na ficha e **obedecer** o que está escrito nela.

---

### Passo 6 — O segurança (senha + catraca)

**Arquivo:** `src/models/seguranca.py`

> 💂 **Analogia:** o segurança tem **três trabalhos**:
> 1. Embaralhar a senha na hora de cadastrar (`gerar_hash`)
> 2. Conferir se a senha digitada bate com a embaralhada (`verificar_senha`)
> 3. Instalar **catracas** nas páginas (`login_obrigatorio` e `so_perfil`)

```python
import bcrypt  # traz a ferramenta que embaralha senhas com segurança (o forno do "bolo")
from functools import wraps  # ajudante pra criar catracas sem bagunçar o nome das funções
from flask import session, redirect  # session = a "pulseira"; redirect = "leve a pessoa para outro endereço"

def gerar_hash(senha):  # recebe a senha de verdade e devolve ela embaralhada (usada só no cadastro)
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()  # encode = vira bytes; gensalt = tempero aleatório (duas senhas iguais ficam diferentes); hashpw = assa o bolo; decode = volta pra texto

def verificar_senha(senha, hash_salvo):  # confere se a senha digitada combina com a embaralhada guardada
    return bcrypt.checkpw(senha.encode(), hash_salvo.encode())  # refaz o "bolo" com a senha digitada e compara com o bolo guardado; devolve True ou False

def login_obrigatorio(f):  # CATRACA 1: só passa quem tem pulseira (fez login). "f" é a página protegida
    @wraps(f)  # mantém o nome original da página (evita confusão interna do Flask)
    def verificar(*args, **kwargs):  # esta função roda ANTES da página abrir
        if "usuario_id" not in session:  # olha o pulso: tem pulseira com o número do usuário?
            return redirect("/")  # NÃO tem: manda de volta pra tela de login
        return f(*args, **kwargs)  # TEM: libera a catraca e abre a página normalmente
    return verificar  # devolve a página já com a catraca instalada na frente

def so_perfil(*perfis):  # CATRACA 2: só passa quem tem a cor de crachá certa; aceita um ou mais perfis
    def decorador(f):  # "f" é a página protegida
        @wraps(f)  # mantém o nome original da página
        def verificar(*args, **kwargs):  # roda ANTES da página abrir
            if session.get("perfil") not in perfis:  # a cor do crachá (perfil) está na lista dos permitidos?
                return "Acesso negado", 403  # NÃO está: mostra "Acesso negado" (403 = código de "proibido")
            return f(*args, **kwargs)  # ESTÁ: libera e abre a página
        return verificar  # devolve a página com a catraca
    return decorador  # devolve o instalador de catracas
```

> 🍰 **Por que hash e não criptografia comum?** Criptografia tem volta (abre com a chave). Hash **não tem volta**. Nem o dono do sistema consegue descobrir a senha de ninguém. Para conferir o login, a gente nunca "desembaralha": **embaralha de novo a senha digitada e compara os dois resultados**.

---

### Passo 7 — O recepcionista (app.py)

**Arquivo:** `src/app.py`

> 🧑‍💼 **Analogia:** o `app.py` é o **recepcionista**. Ele não guarda fichas (isso é do arquivista) e não confere senha sozinho (isso é do segurança), mas **sabe chamar cada um na hora certa** e decide pra onde a pessoa vai.

```python
from datetime import timedelta  # ferramenta pra trabalhar com "quantidade de tempo" (ex.: 30 minutos)
from flask import (Flask, render_template, request, redirect,  # traz as peças do Flask: o prédio, entregar HTML, ler formulário, redirecionar...
                   session, send_from_directory, abort)  # ...a pulseira (session), entregar arquivos e "não encontrado" (abort)
from dao.usuario_dao import buscar_por_email  # chama o arquivista
from models.seguranca import verificar_senha, login_obrigatorio, so_perfil  # chama o segurança e as catracas

app = Flask(__name__, template_folder="views", static_folder=None)  # cria o prédio; os HTMLs ficam na pasta "views"; static_folder=None = não abre nenhuma pasta pro público automaticamente
app.secret_key = "troque-por-uma-frase-grande-e-secreta"  # a "tinta secreta" que assina as pulseiras pra ninguém falsificar (troque!)
app.permanent_session_lifetime = timedelta(minutes=30)  # a pulseira vence após 30 min sem uso (regra de segurança)

PAINEIS = {  # tabela "cor do crachá → andar"
    "supervisor": "/supervisor",  # quem é supervisor vai para /supervisor
    "gestor": "/gestor",  # quem é gestor vai para /gestor
    "ti": "/ti",  # quem é técnico de TI vai para /ti
}  # fim da tabela

@app.route("/assets/<path:arquivo>")  # endereço pra entregar CSS, JS e imagens (ex.: /assets/paginaLogin.css)
def assets(arquivo):  # função que atende esse endereço; "arquivo" é o caminho pedido
    if arquivo.endswith(".html"):  # se pediram um arquivo .html por aqui...
        abort(404)  # ...diz "não existe": páginas HTML só abrem pelas rotas protegidas, senão burlariam o login
    return send_from_directory("views", arquivo)  # entrega o arquivo pedido, de dentro da pasta views

@app.route("/")  # endereço da página inicial (http://localhost:5000/)
def tela_login():  # o que fazer quando alguém chegar na porta de entrada
    return render_template("index.html")  # entrega a tela de login

@app.route("/login", methods=["POST"])  # endereço que RECEBE o formulário (POST = dados enviados escondidos, não na barra do navegador)
def fazer_login():  # o que fazer quando alguém clicar em "Entrar"
    email = request.form["email"]  # lê o campo e-mail que a pessoa digitou
    senha = request.form["senha"]  # lê o campo senha
    perfil_escolhido = request.form["perfil"]  # lê qual aba estava marcada (supervisor, gestor ou ti)

    usuario = buscar_por_email(email)  # pede pro arquivista trazer a ficha desse e-mail

    if (usuario is None  # NÃO achou ninguém com esse e-mail?
            or not verificar_senha(senha, usuario["senha_hash"])  # OU a senha digitada não bate com a embaralhada?
            or usuario["perfil"] != perfil_escolhido):  # OU o perfil real é diferente da aba escolhida?
        return render_template("index.html", erro="E-mail ou senha inválidos")  # qualquer falha: mostra a MESMA mensagem (não revela qual dado errou)

    session.permanent = True  # liga o relógio de 30 min da pulseira
    session["usuario_id"] = usuario["id"]  # coloca na pulseira o número do usuário
    session["perfil"] = usuario["perfil"]  # coloca na pulseira a cor do crachá (vem do BANCO, não da aba!)
    return redirect(PAINEIS[usuario["perfil"]])  # leva a pessoa para o andar do perfil dela

@app.route("/sair")  # endereço de logout
def sair():  # o que fazer quando alguém clicar em "Sair"
    session.clear()  # arranca a pulseira (apaga tudo da sessão)
    return redirect("/")  # devolve a pessoa pra porta de entrada

@app.route("/supervisor")  # endereço do painel do supervisor
@login_obrigatorio  # CATRACA 1: precisa ter feito login
@so_perfil("supervisor")  # CATRACA 2: precisa ser supervisor
def painel_supervisor():  # o que mostrar quando passar nas duas catracas
    return render_template("supervisor/index.html")  # entrega o HTML do painel (ajuste o nome do arquivo)

@app.route("/gestor")  # endereço do painel do gestor
@login_obrigatorio  # CATRACA 1: precisa ter feito login
@so_perfil("gestor")  # CATRACA 2: precisa ser gestor
def painel_gestor():  # o que mostrar quando passar nas duas catracas
    return render_template("dashboard_gestor/index.html")  # entrega o HTML do painel (ajuste o nome do arquivo)

@app.route("/ti")  # endereço do painel do técnico de TI
@login_obrigatorio  # CATRACA 1: precisa ter feito login
@so_perfil("ti")  # CATRACA 2: precisa ser técnico de TI
def painel_ti():  # o que mostrar quando passar nas duas catracas
    return "Painel do Técnico TI (em construção)"  # provisório até alguém criar a tela

if __name__ == "__main__":  # só roda o que vem abaixo se você executar ESTE arquivo diretamente
    app.run(debug=True)  # liga o prédio em http://localhost:5000 (debug=True: avisa os erros e reinicia sozinho; desligar em produção)
```

> 🔑 **O detalhe mais importante deste arquivo:** o perfil que vai pra pulseira vem do **banco** (`usuario["perfil"]`), nunca da aba que a pessoa clicou. A aba só serve como **conferência**. Se a gente confiasse na aba, qualquer um clicaria em "Gestor" e entraria como gestor.

> 🔒 **E o JavaScript?** Poderíamos esconder botões com JS, mas isso é só aparência: qualquer pessoa consegue mexer no JS do próprio navegador. **Quem manda de verdade é o Python**, no servidor.

---

### Passo 8 — Ajustar o `index.html`

**Arquivo:** `src/views/index.html` (o que já existe)

São **3 mudanças**. Não precisa refazer a tela, só ajustar estes pontos.

#### Mudança A — Caminho do CSS e das imagens

> 🗺️ **Analogia:** antes o HTML abria os arquivos direto do computador. Agora quem entrega tudo é o prédio (Flask), então os endereços passam a começar com `/assets/`.

```html
<!-- ANTES -->
<link rel="stylesheet" href="paginaLogin.css">
<img src="img/logo.png">

<!-- DEPOIS -->
<link rel="stylesheet" href="/assets/paginaLogin.css">  <!-- pede o CSS ao servidor, pelo endereço /assets/ -->
<img src="/assets/img/logo.png">                         <!-- pede a imagem ao servidor, também por /assets/ -->
```

> Vale para **todo** CSS, JS e imagem. Os outros integrantes também precisam usar `/assets/` nas telas deles (ex.: `/assets/supervisor/estilo.css`).

#### Mudança B — O formulário

> 📝 **Analogia:** o `<form>` é a **ficha de visitante**. O `action` diz pra qual guichê entregar a ficha, e o `method="POST"` diz "entregue em mãos, não grite na rua".

```html
<form action="/login" method="POST">  <!-- ao enviar, entrega os dados pra rota /login do Python, de forma escondida -->

    <input type="hidden" name="perfil" id="perfil" value="supervisor">  <!-- campo INVISÍVEL que guarda a aba escolhida; começa em "supervisor" -->

    <label for="email">E-mail corporativo</label>  <!-- texto que aparece em cima do campo -->
    <input type="email" id="email" name="email" required>  <!-- campo do e-mail; name="email" é o nome que o Python lê; required = não deixa enviar vazio -->

    <label for="senha">Senha</label>  <!-- texto que aparece em cima do campo -->
    <input type="password" id="senha" name="senha" required>  <!-- campo da senha (mostra bolinhas); name="senha" é o nome que o Python lê -->

    {% if erro %}  <!-- (Flask) SE o Python mandou uma mensagem de erro... -->
        <p class="erro">{{ erro }}</p>  <!-- ...mostra ela aqui (ex.: "E-mail ou senha inválidos") -->
    {% endif %}  <!-- (Flask) fim do "SE" -->

    <button type="submit">Entrar na operação →</button>  <!-- botão que envia a ficha -->
</form>
```

> ⚠️ O `name="..."` de cada campo precisa ser **igualzinho** ao que o Python lê em `request.form["..."]`. Se estiver diferente, dá erro.

#### Mudança C — As abas (Supervisor / Gestor / Técnico TI)

> 🎨 **Analogia:** quando a pessoa clica numa aba, é como se **trocasse a cor da etiqueta** na ficha. O JS só atualiza o campo invisível `perfil`.

Primeiro, em cada botão de aba, adicione `type="button"` (pra ele **não** enviar o formulário) e um `data-perfil`:

```html
<button type="button" data-perfil="supervisor" class="ativa">Supervisor</button>  <!-- aba 1; type="button" = só clica, não envia; data-perfil = o valor que será guardado -->
<button type="button" data-perfil="gestor">Gestor</button>                        <!-- aba 2 -->
<button type="button" data-perfil="ti">Técnico TI</button>                        <!-- aba 3 -->
```

> Use no lugar de `ativa` a classe que o **seu CSS** já usa pra deixar a aba destacada.

Depois, no final do `index.html`, antes de `</body>`:

```html
<script>  <!-- começa o código JavaScript -->
    const abas = document.querySelectorAll("[data-perfil]");  // pega TODOS os botões que têm data-perfil (as 3 abas)
    const campoPerfil = document.getElementById("perfil");  // pega o campo invisível onde guardamos a escolha

    abas.forEach(function (aba) {  // para CADA aba...
        aba.addEventListener("click", function () {  // ...fique de olho: quando alguém clicar nela...
            campoPerfil.value = aba.dataset.perfil;  // ...guarda no campo invisível o perfil daquela aba (supervisor, gestor ou ti)
            abas.forEach(function (a) {  // depois, passa por todas as abas...
                a.classList.remove("ativa");  // ...tirando o destaque de todas
            });
            aba.classList.add("ativa");  // e destaca só a que foi clicada
        });
    });
</script>  <!-- fim do JavaScript -->
```

> 📌 Se o seu HTML ou JS tiver `{{` ou `{%` escritos de outro jeito (ex.: em templates JS), o Flask pode estranhar. Se acontecer, avise o grupo.

---

### Passo 9 — Cadastrar o primeiro usuário

> 🧪 **Por quê?** Sem ninguém no banco, ninguém consegue logar. E não dá pra inserir a senha "na mão" no banco, porque ela precisa ser embaralhada (hash). Este script faz isso.

**Arquivo:** `src/migrations/criar_usuario_inicial.py`

```python
import getpass  # ferramenta pra digitar a senha SEM ela aparecer na tela
from factory.conexao import conectar  # pega o telefone do banco
from models.seguranca import gerar_hash  # pega a função que embaralha a senha (o forno)

PERFIS_VALIDOS = ("supervisor", "gestor", "ti")  # a lista das cores de crachá que existem

nome = input("Nome: ")  # pergunta o nome e guarda a resposta
email = input("E-mail: ")  # pergunta o e-mail
senha = getpass.getpass("Senha: ")  # pergunta a senha (sem mostrar o que digita)
perfil = input("Perfil (supervisor/gestor/ti): ")  # pergunta o perfil

if perfil not in PERFIS_VALIDOS:  # se o perfil digitado não estiver na lista...
    raise SystemExit("Perfil inválido.")  # ...para tudo e avisa o erro

senha_hash = gerar_hash(senha)  # embaralha a senha (vira o "bolo" que não tem volta)

con = conectar()  # liga pro banco
cur = con.cursor()  # pega a caneta
cur.execute(  # manda a ordem pro banco
    "INSERT INTO usuarios (nome, email, senha_hash, perfil) "  # "coloque uma nova ficha na tabela usuarios com estes campos..."
    "VALUES (%s, %s, %s, %s)",  # "...e estes valores" (4 espaços reservados SEGUROS)
    (nome, email, senha_hash, perfil)  # os 4 valores, na mesma ordem dos campos acima
)  # fim da ordem
con.commit()  # CONFIRMA a gravação (sem isso, o banco "esquece" o que foi inserido)
cur.close()  # larga a caneta
con.close()  # desliga o telefone
print("Usuário criado com sucesso!")  # avisa que deu certo
```

Para rodar (dentro da pasta `src`):

```bash
python -m migrations.criar_usuario_inicial
```

---

## 7. Como testar

Faça nesta ordem e marque ✅:

- [ ] Tabela `usuarios` criada no banco
- [ ] Usuário de teste cadastrado com o script do Passo 9
- [ ] Dentro da pasta `src`, rodar `python app.py`
- [ ] Abrir `http://localhost:5000` (**não** abrir o `index.html` com duplo clique)
- [ ] A tela de login aparece **com CSS e imagens** (se estiver sem estilo, confira os `/assets/`)
- [ ] Login certo, com a aba certa → cai no painel do perfil
- [ ] Login certo, com a aba **errada** → mostra "E-mail ou senha inválidos"
- [ ] Senha errada → mostra "E-mail ou senha inválidos"
- [ ] Digitar `http://localhost:5000/gestor` **sem logar** → volta pro login
- [ ] Logado como supervisor, digitar `/gestor` → "Acesso negado"
- [ ] Digitar `/sair` → desloga e volta pro login

---

## 8. Regras de segurança

### ✅ Já implementadas neste passo a passo

| Regra | Onde está | Analogia |
|---|---|---|
| Senha nunca é guardada de verdade (só o hash) | `gerar_hash` / coluna `senha_hash` | Guardar o bolo pronto, não a receita |
| Mensagem de erro sempre igual | `fazer_login` | O segurança diz "não pode entrar" sem explicar o motivo |
| Perfil vem do banco, não da aba | `fazer_login` | Quem define a cor do crachá é o RH, não o visitante |
| Proteção contra SQL Injection (`%s`) | `usuario_dao.py` | O arquivista lê a ficha, não obedece ela |
| Usuário bloqueado não entra (`ativo = 1`) | `usuario_dao.py` | Crachá cancelado não abre a porta |
| Páginas protegidas exigem login | `@login_obrigatorio` | Catraca 1 |
| Cada perfil só abre o próprio painel | `@so_perfil(...)` | Catraca 2 |
| Sessão expira em 30 min parado | `permanent_session_lifetime` | A pulseira tem prazo de validade |
| Botão de sair apaga a sessão | rota `/sair` | Devolver a pulseira na saída |
| Arquivos `.html` não abrem pelo `/assets/` | rota `assets` | Não deixar a porta dos fundos aberta |

### ⏳ Ainda por fazer (futuro)

| Regra | O que é |
|---|---|
| Bloquear após várias tentativas erradas | Ex.: 5 erros = espera 5 minutos (evita adivinhar senha) |
| Autenticação em duas etapas | O botão "Autenticar com código seguro" da tela |
| Senha secreta fora do código | Mover `secret_key` e senha do banco para um arquivo `.env` |
| Rodar com HTTPS | Em produção, a conexão precisa ser criptografada |
| Registro de acessos (log) | Anotar quem entrou e quando |

---

## 9. Erros comuns

| O que aparece | Provável causa | Como resolver |
|---|---|---|
| Tela de login sem CSS / sem imagens | Caminhos sem `/assets/` | Trocar `href="paginaLogin.css"` por `href="/assets/paginaLogin.css"` |
| `ModuleNotFoundError: No module named 'dao'` | Rodou o `app.py` fora da pasta `src` | Entrar na pasta `src` e rodar `python app.py` |
| `ModuleNotFoundError: flask` | Faltou instalar | `pip install flask bcrypt mysql-connector-python` |
| `KeyError: 'email'` | O `name` do campo no HTML é diferente do Python | Conferir `name="email"`, `name="senha"` e `name="perfil"` |
| `TemplateNotFound` | Nome ou caminho do HTML errado | Conferir o nome do arquivo dentro de `views/` |
| Clicar numa aba envia o formulário | Faltou `type="button"` nas abas | Colocar `type="button"` nos 3 botões |
| Login certo mas "E-mail ou senha inválidos" | Senha cadastrada sem hash, ou usuário com `ativo = 0` | Recadastrar pelo script do Passo 9 |
| Abrir o `index.html` com duplo clique | O Python não está no meio | Usar sempre `http://localhost:5000` |

---

## 10. Próximos passos

1. Combinar com o grupo os **nomes dos arquivos HTML** de cada painel (para o `app.py` apontar certo).
2. Combinar que **todos** usem `/assets/` nos caminhos de CSS, JS e imagens.
3. Pedir pra cada integrante colocar `@login_obrigatorio` e `@so_perfil(...)` nas rotas que criar.
4. Implementar o **bloqueio por tentativas** e a **autenticação em duas etapas**.
5. Mover as senhas e a `secret_key` para um arquivo `.env`.

---

*Documento criado para fins de estudo e documentação do projeto ATALAIA 4.0.*
