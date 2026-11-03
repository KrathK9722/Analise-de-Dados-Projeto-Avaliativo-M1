"""Download automatizado/chunks/carga literal das tabelas Raw"""

import logging
import zipfile
from pathlib import Path
import gdown
import pandas as pd
from psycopg2 import sql
from psycopg2.extras import execute_values
from banco import conectar
from config import DATA_DIR, DRIVE_FOLDER_URL, DRIVE_FILE_ID

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
ARQUIVOS = {'2025_Viagem.csv': 'raw_viagem', '2025_Pagamento.csv': 'raw_pagamento', '2025_Passagem.csv': 'raw_passagem', '2025_Trecho.csv': 'raw_trecho',}

def baixar_zip():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = DATA_DIR / 'viagens_2025_6meses.zip'
    if DRIVE_FILE_ID:
        logging.info('Baixando arquivo pelo ID fornecido no .env')
        retorno = gdown.download(id=DRIVE_FILE_ID, output=str(destino), quiet=False)
        if retorno is None:
            raise RuntimeError('Falha no download do arquivo pelo ID')
    else:
        logging.info('Baixando pasta publica do SENAI')
        retornos = gdown.download_folder(url=DRIVE_FOLDER_URL, output=str(DATA_DIR), quiet=False, remaining_ok=True)
        if not retornos:
            raise RuntimeError('Download da pasta falhou ou não retornou arquivos')
        candidatos = list(DATA_DIR.rglob('viagens_2025_6meses.zip'))
        if not candidatos:
            raise FileNotFoundError('ZIP esperado nao foi encontrado após download')
        destino = candidatos[0]
    if not zipfile.is_zipfile(destino):
        raise ValueError('Arquivo baixado não é um ZIP válido')
    return destino

def inserir_arquivo(zip_ref, nome, tabela, conexao):
    with zip_ref.open(nome) as arquivo:
        pedacos = pd.read_csv(arquivo, sep=';', encoding='latin-1', dtype=str,
                              keep_default_na=False, chunksize=5000)
        inseridos = 0
        for bloco in pedacos:
            # A ordem e os nomes das colunas RAW são reproduzidos exatamente.
            colunas = list(bloco.columns)
            valores = [tuple(linha) for linha in bloco.itertuples(index=False, name=None)]
            comando = sql.SQL('INSERT INTO {} ({}) VALUES %s').format(
                sql.Identifier(tabela),
                sql.SQL(', ').join(sql.Identifier(c) for c in colunas)
            )
            with conexao.cursor() as cursor:
                execute_values(cursor, comando.as_string(conexao), valores, page_size=1000)
            inseridos += len(bloco)
        logging.info('%s: %s registros carregados', tabela, inseridos)

def main():
    zip_path = baixar_zip()
    with conectar() as conexao:
        try:
            with conexao.cursor() as cursor:
                cursor.execute('TRUNCATE TABLE raw_viagem, raw_pagamento, raw_passagem, raw_trecho')
            with zipfile.ZipFile(zip_path) as zip_ref:
                nomes = {Path(p).name: p for p in zip_ref.namelist()}
                for nome, tabela in ARQUIVOS.items():
                    if nome not in nomes:
                        raise FileNotFoundError(f'{nome} ausente no ZIP')
                    inserir_arquivo(zip_ref, nomes[nome], tabela, conexao)
            conexao.commit()
        except Exception:
            conexao.rollback()
            logging.exception('Falha na extração, transação revertida')
            raise

if __name__ == '__main__':
    main()
