"""Conveção das quatro tabelas Raw em Silver e registrando linhas inválidas."""
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from psycopg2 import sql
from psycopg2.extras import execute_values
from banco import conectar

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

MAPAS = {
 'silver_viagem': {
  'id_viagem':'Identificador do processo de viagem',
  'num_proposta':'Número da Proposta (PCDP)', 'situacao':'Situação',
  'viagem_urgente':'Viagem Urgente', 'cod_orgao_superior':'Código do órgão superior',
  'nome_orgao_superior':'Nome do órgão superior', 'nome_viajante':'Nome',
  'cargo':'Cargo', 'data_inicio':'Período - Data de início',
  'data_fim':'Período - Data de fim', 'destinos':'Destinos', 'motivo':'Motivo',
  'valor_diarias':'Valor diárias', 'valor_passagens':'Valor passagens',
  'valor_devolucao':'Valor devolução', 'valor_outros_gastos':'Valor outros gastos',
 },
 'silver_pagamento': {
  'id_viagem':'Identificador do processo de viagem',
  'num_proposta':'Número da Proposta (PCDP)',
  'nome_orgao_pagador':'Nome do órgao pagador',
  'nome_ug_pagadora':'Nome da unidade gestora pagadora',
  'tipo_pagamento':'Tipo de pagamento', 'valor':'Valor',
 },
 'silver_passagem': {
  'id_viagem':'Identificador do processo de viagem',
  'meio_transporte':'Meio de transporte',
  'pais_origem_ida':'País - Origem ida', 'uf_origem_ida':'UF - Origem ida',
  'cidade_origem_ida':'Cidade - Origem ida',
  'pais_destino_ida':'País - Destino ida', 'uf_destino_ida':'UF - Destino ida',
  'cidade_destino_ida':'Cidade - Destino ida',
  'valor_passagem':'Valor da passagem', 'taxa_servico':'Taxa de serviço',
  'data_emissao':'Data da emissão/compra',
 },
 'silver_trecho': {
  'id_viagem':'Identificador do processo de viagem ',
  'sequencia_trecho':'Sequência Trecho', 'origem_data':'Origem - Data',
  'origem_uf':'Origem - UF', 'origem_cidade':'Origem - Cidade',
  'destino_data':'Destino - Data', 'destino_uf':'Destino - UF',
  'destino_cidade':'Destino - Cidade', 'meio_transporte':'Meio de transporte',
  'numero_diarias':'Número Diárias',
 },
}
LIMITES = {
 'id_viagem':20, 'num_proposta':20, 'situacao':50, 'viagem_urgente':5,
 'cod_orgao_superior':20, 'nome_orgao_superior':255, 'nome_viajante':255,
 'cargo':255, 'destinos':4000, 'motivo':4000,
 'nome_orgao_pagador':255, 'nome_ug_pagadora':255, 'tipo_pagamento':50,
 'meio_transporte':50, 'pais_origem_ida':60, 'uf_origem_ida':40,
 'cidade_origem_ida':80, 'pais_destino_ida':60, 'uf_destino_ida':40,
 'cidade_destino_ida':80, 'origem_uf':40, 'origem_cidade':80,
 'destino_uf':40, 'destino_cidade':80,
}
MONETARIOS = {'valor_diarias','valor_passagens','valor_devolucao',
              'valor_outros_gastos','valor','valor_passagem','taxa_servico','numero_diarias'}
DATAS = {'data_inicio','data_fim','data_emissao','origem_data','destino_data'}


def texto(valor, limite=None):
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    if limite and len(s) > limite:
        raise ValueError(f'texto com {len(s)} caracteres excede VARCHAR({limite})')
    return s


def decimal_br(valor):
    s = texto(valor)
    if s is None:
        return None
    s = s.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        numero = Decimal(s)
        if not numero.is_finite():
            raise ValueError('decimal não finito')
        return numero.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError) as erro:
        raise ValueError(f'valor numérico inválido: {valor!r}') from erro


def data_br(valor):
    s = texto(valor)
    if not s:
        return None
    try:
        return datetime.strptime(s, '%d/%m/%Y').date()
    except ValueError as erro:
        raise ValueError(f'data inválida: {s!r}') from erro


def inteiro(valor):
    s = texto(valor)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError as erro:
        raise ValueError(f'inteiro inválido: {s!r}') from erro


def transformar(registro, destino, ids_validos):
    mapa = MAPAS[destino]
    convertido = {}
    for campo, origem in mapa.items():
        valor = registro[origem]
        if campo in MONETARIOS:
            convertido[campo] = decimal_br(valor)
        elif campo in DATAS:
            convertido[campo] = data_br(valor)
        elif campo == 'sequencia_trecho':
            convertido[campo] = inteiro(valor)
        else:
            convertido[campo] = texto(valor, LIMITES.get(campo))

    identificador = convertido['id_viagem']
    if not identificador:
        raise ValueError('id_viagem vazio')
    if destino == 'silver_viagem':
        if not convertido['nome_orgao_superior']:
            raise ValueError('nome_orgao_superior obrigatório')
        inicio, fim = convertido['data_inicio'], convertido['data_fim']
        if inicio and fim and fim < inicio:
            raise ValueError('data_fim anterior a data_inicio')
        convertido['duracao_dias'] = (fim - inicio).days + 1 if inicio and fim else None
        valores = [convertido[campo] or Decimal('0') for campo in (
            'valor_diarias','valor_passagens','valor_outros_gastos','valor_devolucao')]
        convertido['valor_total'] = valores[0] + valores[1] + valores[2] - valores[3]
    else:
        if identificador not in ids_validos:
            raise ValueError('viagem sem registro pai na Silver')
        if destino == 'silver_pagamento' and not convertido['tipo_pagamento']:
            raise ValueError('tipo_pagamento obrigatório')
        if destino == 'silver_trecho' and convertido['sequencia_trecho'] is None:
            raise ValueError('sequencia_trecho obrigatório para UNIQUE')
    for campo in MONETARIOS & set(convertido):
        valor = convertido[campo]
        if valor is not None:
            if campo in ('valor_diarias','valor','valor_passagem','taxa_servico','numero_diarias') and valor < 0:
                raise ValueError(f'{campo} negativo viola CHECK')
            if abs(valor) >= Decimal('100000000'):
                raise ValueError(f'{campo} excede DECIMAL(10,2)')
    if destino == 'silver_viagem' and abs(convertido['valor_total']) >= Decimal('10000000000'):
        raise ValueError('valor_total excede DECIMAL(12,2)')
    return convertido


def carregar(raw, silver, ids_validos):
    mapa = MAPAS[silver]
    campos = list(mapa)

    colunas = sql.SQL(', ').join(
        sql.Identifier(c) for c in campos
    )

    comando = sql.SQL(
        'INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING'
    ).format(
        sql.Identifier(silver),
        colunas
    )

    erros = 0
    validos = 0
    exemplos = []

    with conectar() as conexao:
        with conexao.cursor() as leitor:
            leitor.execute(
                sql.SQL('SELECT * FROM {}').format(
                    sql.Identifier(raw)
                )
            )

            if leitor.description is None:
                raise RuntimeError(
                    f'A consulta da tabela {raw} não retornou colunas.'
                )

            nomes = [d.name for d in leitor.description]

            while True:
                linhas = leitor.fetchmany(5000)

                if not linhas:
                    break

                lote = []

                for linha in linhas:
                    registro = dict(zip(nomes, linha))

                    try:
                        convertido = transformar(
                            registro, silver, ids_validos
                        )

                        lote.append(
                            tuple(convertido[c] for c in campos)
                        )

                    except (ValueError, KeyError, TypeError) as erro:
                        erros += 1

                        if len(exemplos) < 5:
                            exemplos.append(str(erro))

                if lote:
                    with conexao.cursor() as escritor:
                        execute_values(
                            escritor,
                            comando.as_string(conexao),
                            lote,
                            page_size=1000
                        )

                    validos += len(lote)

    logging.info(
        '%s: %s linhas validadas; %s rejeitadas. Exemplos: %s',
        silver, validos, erros, exemplos
    )

def main():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute('TRUNCATE silver_trecho, silver_passagem, silver_pagamento, silver_viagem RESTART IDENTITY')
    carregar('raw_viagem', 'silver_viagem', set())
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute('SELECT id_viagem FROM silver_viagem')
            ids_validos = {r[0] for r in cursor.fetchall()}
    logging.info('Viagens pai válidas: %s', len(ids_validos))
    for raw, silver in [
        ('raw_pagamento','silver_pagamento'),
        ('raw_passagem','silver_passagem'),
        ('raw_trecho','silver_trecho'),
    ]:
        carregar(raw, silver, ids_validos)

if __name__ == '__main__':
    main()
