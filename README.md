# ATALAIA 4.0 — Centro de Inteligência Operacional

Sistema de vigilância com visão computacional para detecção de EPIs e conformidade em ambiente industrial.

## Estrutura

```
Atalaia 4.0/
├── gui/              # Front-end (HTML / CSS / JS)
│   ├── index.html    # Página de login
│   ├── supervisor/   # Dashboard do supervisor
│   └── dashboard_gestor/  # Dashboard do gestor
├── dao/              # Acesso ao banco de dados (a criar)
├── factory/          # Fábricas / injeção de dependência (a criar)
├── model/            # Modelos de domínio / entidades (a criar)
└── migrations/       # Scripts de migração do banco (a criar)
```

## Como rodar

### Front-end
Abrir `gui/index.html` no navegador (sem servidor necessário para desenvolvimento).

### Back-end (a implementar)
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py                  # ponto de entrada (a criar)
```

### Treinar o modelo (a implementar)
```bash
# Configurar dataset em datasets/ (ignorado pelo git)
python train.py
```

## Tecnologias
- **Front-end:** HTML5, CSS3, JavaScript
- **Back-end:** Python 3.11+
- **Visão computacional:** OpenCV + YOLOv8 (planejado)
