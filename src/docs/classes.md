# Guia Definitivo: Criando Classes no Projeto ATALAIA 4.0

Este documento explica de forma simples e direta como construir a camada de **Modelos (Models)** do seu projeto, utilizando o padrão MVC e banco de dados MySQL.

---

## 1. O Conceito de ORM (Object-Relational Mapping)

O **ORM** é como um tradutor simultâneo. 
No mundo ideal, o Python não sabe o que é uma tabela de banco de dados, e o MySQL não sabe o que é uma classe Python. O ORM (SQLAlchemy) fica no meio dos dois.

*   **Sem ORM:** Você escreve SQL puro em todo lugar (`SELECT * FROM Camera WHERE status = 'ativa'`).
*   **Com ORM:** Você manipula classes e objetos em Python, e o ORM gera o SQL sozinho (`db.query(Camera).filter(Camera.status == 'ativa')`).

Para ativar esse "poder", toda classe precisa herdar de uma classe especial chamada **`Base`**. É ela que avisa o SQLAlchemy: *"Transforme essa classe em uma tabela no MySQL"*.

---

## 2. As Classes em Si (Modelos)

Vamos ver como criar a classe `Setor`. Note que **cada linha** possui um comentário explicando o seu propósito.

```python
# Importamos as ferramentas que representam os tipos de dados no SQL
from sqlalchemy import Column, Integer, String, Text, Enum

# Importamos a Base (a 'Certidão de Nascimento' que conecta com o banco)
from src.factory.database import Base 

# 1. Definimos a classe que representa a tabela. Ela HERDA a Base.
class Setor(Base):
    
    # 2. Informamos o nome EXATO da tabela que já existe no MySQL
    __tablename__ = "Setor"

    # 3. Criamos a coluna do ID. 
    # Integer = Número inteiro
    # primary_key=True = É a chave primária
    # autoincrement=True = O banco preenche sozinho (1, 2, 3...)
    id_setor = Column(Integer, primary_key=True, autoincrement=True)

    # 4. Criamos a coluna do nome do setor.
    # String(50) = VARCHAR(50)
    # nullable=False = Equivalente a NOT NULL (não pode ficar vazio)
    nome_setor = Column(String(50), nullable=False)

    # 5. Coluna de descrição. 
    # Text = Campo de texto longo
    # nullable=True = Pode ficar vazio (não tem NOT NULL no SQL)
    descricao = Column(Text, nullable=True)

    # (Os relacionamentos vêm no próximo passo!)
```

---

## 3. Associações (Relacionamentos e Chaves Estrangeiras)

As associações são os "links" entre as tabelas. No SQL, usamos a `FOREIGN KEY` (Chave Estrangeira). No Python, usamos o `relationship` para podermos "clicar" e navegar entre os objetos (ex: `incidente.camera.setor`).

Existem dois tipos principais no seu projeto: **1 para N** e **N para M**.

### A) Associação 1:N (Um Setor tem Várias Câmeras)
Veja como criamos a classe `Camera` associada ao `Setor`:

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.factory.database import Base

class Camera(Base):
    __tablename__ = "Camera"

    id_camera = Column(Integer, primary_key=True, autoincrement=True)
    codigo_identificador = Column(String(50), nullable=False)

    # 1. CHAVE ESTRANGEIRA (A visão do Banco de Dados)
    # ForeignKey("Setor.id_setor") diz que este número aponta para o ID da tabela Setor
    fk_Setor_id_setor = Column(Integer, ForeignKey("Setor.id_setor"), nullable=False)

    # 2. RELATIONSHIP (A visão do Python - Navegação fácil)
    # Diz ao Python: "Crie um link mágico chamado 'setor' que busca os dados na classe 'Setor'"
    # back_populates avisa a classe Setor que essa relação existe do lado de cá também.
    setor = relationship("Setor", back_populates="cameras")
```

### B) Associação N:M (Vários Setores <-> Vários Usuários)
Quando um Setor tem vários Usuários e um Usuário tem vários Setores, precisamos de uma **tabela intermediária** (`setor_usuario`). Como ela não tem dados próprios, só chaves, declaramos ela como uma `Table` direta:

```python
from sqlalchemy import Table, Column, Integer, ForeignKey
from src.factory.database import Base

# Criamos a tabela associativa puramente estrutural
setor_usuario = Table(
    # 1. Nome da tabela no banco
    "setor_usuario",
    
    # 2. Vincula à Base
    Base.metadata,
    
    # 3. Coluna que aponta para o Setor (e é chave primária)
    Column("fk_Setor_id_setor", Integer, ForeignKey("Setor.id_setor"), primary_key=True),
    
    # 4. Coluna que aponta para o Usuário (e é chave primária)
    Column("fk_Usuarios_id_usuario", Integer, ForeignKey("Usuarios.id_usuario"), primary_key=True)
)
```

Na classe `Usuario`, o relacionamento fica assim:
```python
    # Mostra ao Python para usar a tabela 'setor_usuario' (secondary) para achar os Setores
    setores = relationship("Setor", secondary=setor_usuario, back_populates="usuarios")
```

---

## 4. O Arquivo `__init__.py`

Se você olhar a sua pasta `src/models/`, terá vários arquivos: `setor.py`, `usuario.py`, `camera.py`, etc. 

O arquivo **`__init__.py`** (com dois underlines de cada lado) é o **Índice da Pasta**. 
Ele avisa ao Python que a pasta `models` é um "módulo" (um pacote oficial de código) e centraliza todas as importações para facilitar a sua vida.

Veja o que você escreve dentro de `src/models/__init__.py`:

```python
# Importa do arquivo setor.py a classe Setor
from .setor import Setor

# Importa do arquivo usuario.py a classe Usuario
from .usuario import Usuario

# Importa do arquivo camera.py a classe Camera
from .camera import Camera

# Importa do arquivo associacoes.py a tabela associativa
from .associacoes import setor_usuario
```

**Qual a vantagem disso?**
Quando você for criar o seu DAO (na pasta `src/dao/`), você não vai precisar caçar em qual arquivo cada classe está. Você importa tudo de uma vez só da pasta mãe:

```python
# No seu src/dao/incidente_dao.py
# Fica muito mais limpo e organizado!
from src.models import Setor, Usuario, Camera
```