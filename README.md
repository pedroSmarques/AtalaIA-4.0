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

- Python 3.11 ou superior instalado
- MySQL rodando localmente (porta 3306) com um banco chamado `atalaia`

### 2. Criar o ambiente virtual

Abra um terminal na pasta do projeto e execute:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar as dependências

```cmd
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

```cmd
copy .env.example .env
```

Abra o arquivo `.env` e ajuste:

```
JWT_SECRET_KEY=uma-chave-longa-e-aleatoria
DATABASE_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/atalaia
```

### 5. Criar as tabelas e os usuários de teste

Certifique-se de que o banco `atalaia` existe no MySQL, depois rode:

```cmd
python criar_usuarios_teste.py
```

Esse script cria as tabelas automaticamente e solicita as senhas dos usuários de teste.

### 6. Usuários criados

| Cargo | E-mail |
|---|---|
| Gestor | gestor@atalaia.com |
| Supervisor | supervisor@atalaia.com |
| Técnico | tecnico@atalaia.com |

A senha é pedida no terminal (ou gerada e exibida uma única vez).

### 7. Iniciar o servidor

```cmd
python run.py
```

Acesse: **http://localhost:5000**

### 8. Rodar os testes

```cmd
pytest tests/ -v
```

Os testes usam SQLite em memória — não é necessário o MySQL para testá-los.

---

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `JWT_SECRET_KEY` | Chave secreta para assinar os tokens | string aleatória de 64+ chars |
| `DATABASE_URL` | URL de conexão com o banco | `mysql+pymysql://root:@localhost/atalaia` |
| `FLASK_ENV` | Ambiente (`development` ou `production`) | `development` |
| `FLASK_DEBUG` | Modo debug (`1` = ativo) | `1` |

Em produção, defina `FLASK_ENV=production` para ativar os cookies Secure (HTTPS obrigatório).
