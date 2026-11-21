# ATALAIA 4.0 — Centro de Inteligência Operacional

Sistema de vigilância com IA para detecção de infrações de EPI em ambientes industriais.

---

## O que é o projeto

O ATALAIA monitora câmeras de segurança em tempo real, detecta automaticamente situações de risco (capacete ausente, colete faltando, etc.) e alerta os responsáveis. Três perfis de acesso:

| Perfil | O que faz |
|---|---|
| **Gestor** | Visão completa: câmeras, alertas, usuários, setores, relatórios, logs |
| **Supervisor** | Monitora alertas e câmeras (leitura), atende incidentes |
| **Técnico TI** | Gerencia câmeras (edita URL/FPS/status) e consulta logs |

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
│   ├── database.py         # Re-exporta Base do SQLAlchemy
│   ├── erros.py            # Handlers 401/403/404/500
│   ├── autenticacao/       # Login, logout, decoradores, servico
│   └── rotas/              # Blueprints: gestor, supervisor, tecnico
├── src/
│   ├── database.py         # Engine e sessão SQLAlchemy
│   ├── models/             # Tabelas do banco (Usuario, Camera, Incidente...)
│   └── dao/                # Consultas ao banco por entidade
├── templates/              # HTML Jinja2 por perfil
│   ├── login.html
│   ├── gestor/
│   ├── supervisor/
│   ├── tecnico/
│   └── erros/
├── static/                 # CSS e JS servidos pelo Flask
│   ├── css/base.css
│   └── js/base.js
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

Os testes usam SQLite em memória — não é necessário o MySQL para rodá-los.

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
