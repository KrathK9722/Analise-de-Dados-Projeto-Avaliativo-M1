import psycopg2
from psycopg2.extras import execute_values

from config import (
    DB_HOST, DB_PORT, DB_NAME,
    DB_USER, DB_PASSWORD
)


def conectar():
    if not DB_PASSWORD:
        raise RuntimeError("Defina DB_PASSWORD no .env")

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def executar(sql, parametros=None):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)


def inserir_em_lote(cursor, sql, linhas, tamanho=1000):
    if linhas:
        execute_values(
            cursor, sql, linhas, page_size=tamanho
        )
