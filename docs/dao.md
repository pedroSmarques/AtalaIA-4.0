# Guia Definitivo: Criando Arquivos DAO no Projeto ATALAIA 4.0

Este documento explica de forma simples como construir a camada **DAO (Data Access Object)** do seu projeto, onde a mágica do banco de dados realmente acontece.

## 1. O que é um DAO?

Pense no **Model** (que criamos antes) como a "planta de uma casa". Ele diz onde ficam as paredes e as portas, mas não constrói nada sozinho.
O **DAO** é o **"Pedreiro"**. É ele quem pega a planta (o Model) e efetivamente vai lá no banco de dados para **Criar, Ler, Atualizar ou Deletar** informações (o famoso CRUD).

A regra de ouro é: **Toda a comunicação com o banco de dados deve ficar presa dentro do DAO.** Nenhuma outra parte do sistema deve fazer `db.query(...)`.

## 2. A Estrutura Básica de um DAO

Vamos construir o `SetorDAO` (no arquivo `src/dao/setor_dao.py`). 
Abaixo está o código com **cada linha comentada** para você entender exatamente o que está acontecendo:

```python
# 1. Importamos o tipo 'Session', que representa a conexão aberta com o MySQL
from sqlalchemy.orm import Session

# 2. Importamos o Model (a "planta") e os Enums que vamos precisar
from src.models import Setor, NivelRiscoEnum

# 3. Criamos a classe DAO para a tabela Setor
class SetorDAO:
    
    # 4. O método __init__ é chamado assim que o DAO é criado.
    # Ele recebe a 'db' (a conexão com o banco) e guarda para usar depois.
    def __init__(self, db: Session):
        self.db = db

    # ==========================================
    # C - CREATE (Criar / Inserir no Banco)
    # ==========================================
    def criar(self, nome_setor: str, nivel_risco: NivelRiscoEnum, descricao: str = None) -> Setor:
        
        # Passo 1: Criamos o objeto Python usando o nosso Model
        novo_setor = Setor(
            nome_setor=nome_setor,
            nivel_risco=nivel_risco,
            descricao=descricao
        )
        
        # Passo 2: Adicionamos o objeto na "fila" de salvamento do SQLAlchemy
        self.db.add(novo_setor)
        
        # Passo 3: Fazemos o 'commit', que é a ordem real de "Salvar no MySQL!" (Gera o INSERT)
        self.db.commit()
        
        # Passo 4: Atualizamos o objeto para que o MySQL devolva o ID que foi gerado automaticamente
        self.db.refresh(novo_setor)
        
        # Retornamos o objeto prontinho e já com ID
        return novo_setor

    # ==========================================
    # R - READ (Ler / Buscar no Banco)
    # ==========================================
    def buscar_por_id(self, id_setor: int) -> Setor | None:
        
        # Tradução: "No banco (self.db), faça uma busca (query) na tabela Setor,
        # filtre (filter) onde a coluna ID seja igual ao ID passado,
        # e me entregue o primeiro (first) resultado que achar."
        return self.db.query(Setor).filter(Setor.id_setor == id_setor).first()

    def listar_todos(self) -> list[Setor]:
        # Tradução: "Busque todos (all) os registros da tabela Setor"
        return self.db.query(Setor).all()

    # ==========================================
    # U - UPDATE (Atualizar)
    # ==========================================
    def atualizar(self, id_setor: int, novo_nome: str = None) -> Setor | None:
        
        # Passo 1: Primeiro, buscamos se o setor existe usando o método que já criamos
        setor_existente = self.buscar_por_id(id_setor)
        
        # Se não achou, encerra e retorna vazio (None)
        if not setor_existente:
            return None
        
        # Se um novo nome foi enviado, substituímos no objeto Python
        if novo_nome:
            setor_existente.nome_setor = novo_nome

        # Fazemos o 'commit' para o SQLAlchemy ver que algo mudou e gerar o comando UPDATE no MySQL
        self.db.commit()
        
        # Atualizamos o objeto com os dados frescos do banco
        self.db.refresh(setor_existente)
        return setor_existente

    # ==========================================
    # D - DELETE (Deletar)
    # ==========================================
    def deletar(self, id_setor: int) -> bool:
        
        # Passo 1: Busca o setor no banco
        setor_existente = self.buscar_por_id(id_setor)
        
        if not setor_existente:
            return False # Retorna Falso se não encontrou nada para deletar
        
        # Passo 2: Dá a ordem de deleção na fila
        self.db.delete(setor_existente)
        
        # Passo 3: Efetiva a exclusão no MySQL (Gera o DELETE FROM)
        self.db.commit()
        
        return True # Retorna Verdadeiro indicando sucesso
```

## 3. Por que trabalhar assim? (Na Prática)

Quando você for criar a sua tela de cadastro na camada `views`, você não vai precisar se preocupar com comandos de banco de dados. O seu código de visualização ficará muito limpo, parecendo algo assim:

```python
# Faz a conexão e chama o DAO
db_session = SessionLocal()
gerenciador_setor = SetorDAO(db_session)

# O DAO faz todo o trabalho sujo!
gerenciador_setor.criar("Caldeiraria", NivelRiscoEnum.critico)
print("Setor cadastrado com sucesso!")
```