# ATALAIA 4.0 — Centro de Inteligência Operacional

Sistema de vigilância com IA para detecção de infrações de EPI em ambientes industriais.

---

## O que é o projeto

O ATALAIA monitora câmeras de segurança em tempo real, detecta automaticamente situações de risco (capacete ausente, colete faltando, etc.) e alerta os responsáveis. Três perfis de acesso:

| Perfil | O que faz |
|---|---|
| **Gestor** | Visão completa: câmeras, alertas, usuários, setores, relatórios, logs. Cria/edita usuários, setores e câmeras e bloqueia contas |
| **Supervisor** | Monitora alertas e câmeras (leitura), atende incidentes (iniciar, resolver, falso positivo) e gera relatório de incidentes |
| **Técnico TI** | Gerencia câmeras (edita URL/FPS/status), consulta logs e gera relatório de câmeras |

---

## Funcionalidades

- **Meu perfil** (todos os perfis): clique no avatar (topo ou menu). Edite o nome de exibição, a **foto** e a **senha** (pede a senha atual).
  - Foto: JPG, PNG ou WebP até 2 MB. O arquivo é validado pelo **conteúdo** (não pela extensão), recortado em quadrado de 256 px e salvo em WebP com nome aleatório em `static/uploads/avatares/` (fora do git). Sem foto, aparecem as iniciais. A foto aparece no topo, no menu e nas listas de equipe.
  - Cada pessoa altera apenas o próprio perfil.
- **Relatórios em PDF**: todo botão "Gerar PDF" abre um modal com tipo, período e observações, e os botões **Baixar PDF** e **Enviar por e-mail**. O PDF é gerado no servidor (fpdf2) com cabeçalho (logo e nome do sistema), período, indicadores, tabela de incidentes/câmeras, observações e rodapé com data/hora e quem gerou. Cada perfil só gera os relatórios que pode ver.
  - > **Envio por e-mail é SIMULADO.** O sistema valida o destinatário, gera o relatório, mostra "Enviando..." e a confirmação, e registra a ação nos logs, mas **não envia e-mail de verdade**. O envio real (SMTP ou serviço de e-mail) é a próxima etapa; o ponto de troca está marcado em `app/relatorios/rotas.py`.
- **Cadastros**: usuários (criar, editar, bloquear/desbloquear), setores e câmeras (criar, editar). Toda ação fica registrada em **Logs do sistema**.
- **Visual HUD**: transições entre telas (View Transitions), vidro em cabeçalho/menus/modais/avisos, brilho de borda nos cards, avisos (toasts) com barra de tempo. Respeita `prefers-reduced-motion`, `prefers-reduced-transparency` e `prefers-contrast`.

---

## Tecnologia

- **Back-end:** Python 3.11, Flask 3.1, SQLAlchemy 2.0
- **Autenticação:** JWT em cookie HttpOnly via flask-jwt-extended, senhas com bcrypt
- **Banco:** MySQL (configurável via `.env`)
- **Visão Computacional:** YOLOv8 (módulo separado, não coberto aqui)

---

## Estrutura de pastas

```
Atalaia 4.0/
├── app/                    # Pacote Flask (factory, blueprints, auth)
│   ├── __init__.py         # criar_app() — ponto de entrada
│   ├── config.py           # Configuração via .env
│   ├── contexto.py         # Dados do usuário logado para os templates
│   ├── auditoria.py        # Registro de ações nos logs
│   ├── validacao.py        # Validações de formulário (e-mail, CPF, senha)
│   ├── autenticacao/       # Login, logout, decoradores, serviço
│   ├── perfil/             # Meu perfil: nome, foto (Pillow) e senha
│   ├── relatorios/         # Relatórios em PDF (fpdf2) e envio simulado
│   └── rotas/              # Blueprints: gestor, supervisor, tecnico
├── src/
│   ├── database.py         # Engine e sessão SQLAlchemy
│   ├── models/             # Tabelas do banco (Usuario, Camera, Incidente...)
│   ├── dao/                # Consultas ao banco por entidade
│   ├── migrations/         # Script SQL do banco
│   └── views/              # HTML Jinja2 (login, gestor, supervisor, tecnico, perfil, componentes)
├── static/                 # Arquivos servidos pelo Flask
│   ├── css/                # base.css (identidade), hud.css (visual HUD), toast.css, login.css
│   ├── js/                 # base.js, toast.js
│   ├── img/                # logo e imagens
│   └── uploads/avatares/   # fotos de perfil (criada sozinha, ignorada pelo git)
├── tests/                  # Testes automatizados (pytest)
├── docs/                   # Documentação do projeto
├── criar_usuarios_teste.py # Script para criar contas iniciais
├── run.py                  # Inicia o servidor
├── requirements.txt
├── .env.example            # Modelo de variáveis de ambiente
└── .gitignore
```

---

## Como executar no Windows

### 1. Pré-requisitos

- Python 3.11 ou superior (marque **"Add Python to PATH"** na instalação)
- MySQL rodando (se usar XAMPP: abra o painel e clique em **Start** ao lado de MySQL)
- Banco de dados chamado `atalaia` criado no MySQL (via phpMyAdmin ou linha de comando)

### 2. Dois cliques e pronto

Dê dois cliques em **`iniciar.bat`**.

O script vai:
- criar o ambiente virtual automaticamente,
- instalar as dependências,
- gerar o `.env` com chave secreta (só na primeira vez),
- criar as tabelas e os usuários de teste,
- abrir o navegador em **http://localhost:5000**.

Ao final aparece um quadro com os acessos de demonstração, por exemplo:

```
==============================================================
   ACESSOS DE DEMONSTRACAO — ATALAIA 4.0
==============================================================
   Perfil       E-mail                         Senha
   ---------------------------------------------------------
   Gestor       gestor@atalaia.com             Gestor@2024
   Supervisor   supervisor@atalaia.com         Superv@2024

   Tecnico      tecnico@atalaia.com            Tecnico@2024
==============================================================
```

> Para alterar e-mails ou senhas dos usuários de teste, edite as variáveis
> `USUARIO_TESTE_*` no arquivo `.env` e execute **`resetar-usuarios.bat`**.

### 3. Rodar os testes

```cmd
pytest tests/ -v
```

Os testes usam SQLite em memória — não é necessário o MySQL para rodá-los. Cobrem login/logout (com CSRF ligado), perfil e foto, relatórios em PDF, permissões por perfil, cadastros e a abertura de todas as telas com dados.

> **Banco já existente:** a coluna nova `usuarios.foto_perfil` é criada sozinha ao iniciar o app (ou ao rodar `criar_usuarios_teste.py`). O comando equivalente também está no fim de `src/migrations/AtalaIA.sql`.

### 4. Conferir as telas no navegador (opcional)

Para gerar prints e checar a responsividade (360, 390, 768, 1024, 1366 e 1920 px), instale o Playwright:

```cmd
pip install playwright
python -m playwright install chromium
```

---

## Execução manual (avançado)

Se preferir executar passo a passo sem usar o `iniciar.bat`:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edite o `.env` e ajuste `JWT_SECRET_KEY` e `DATABASE_URL`, depois:

```cmd
python criar_usuarios_teste.py
python run.py
```

Acesse: **http://localhost:5000**

---

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `JWT_SECRET_KEY` | Chave secreta para assinar os tokens | string aleatória de 64+ chars |
| `DATABASE_URL` | URL de conexão com o banco | `mysql+pymysql://root:@localhost/atalaia` |
| `FLASK_ENV` | Ambiente (`development` ou `production`) | `development` |
| `FLASK_DEBUG` | Modo debug (`1` = ativo) | `1` |

Em produção, defina `FLASK_ENV=production` para ativar os cookies Secure (HTTPS obrigatório).
