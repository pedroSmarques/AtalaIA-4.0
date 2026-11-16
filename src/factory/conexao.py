import mysql.connector
from mysql.connector import Error

try:
    conexao = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",          # Coloque sua senha aqui
        database="atalaia"  # Coloque o nome do seu banco aqui
    )

    if conexao.is_connected():
        print("Conectado ao MySQL com sucesso!")
        conexao.close()

except Error as erro:
    print(f"Erro ao conectar: {erro}")