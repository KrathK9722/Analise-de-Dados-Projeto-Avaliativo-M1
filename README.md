# Análise de Dados com Python — Projeto Avaliativo SENAI

Pipeline ETL desenvolvido como parte do projeto avaliativo do curso de Análise de Dados com Python, utilizando dados públicos de viagens a serviço do Governo Federal, disponibilizados pelo Portal da Transparência.

O projeto utiliza a arquitetura Medallion (Raw, Silver e Gold) para extrair, armazenar, transformar e analisar dados de viagens, pagamentos, passagens e trechos referentes aos seis meses disponibilizados de 2025.

## 1. Objetivo

Construir um processo ETL capaz de organizar dados públicos em diferentes camadas de tratamento, garantindo maior consistência para consultas e análises.

Ao final, são propostas sete perguntas de negócio, respondidas por meio de consultas SQL, tabelas e visualizações gráficas.

## 2. Arquitetura do projeto

O processamento é dividido em três camadas:

| Camada | Descrição |
|---|---|
| **Raw** | Armazena os dados originais dos arquivos CSV, preservando os valores como texto. |
| **Silver** | Realiza conversões de tipos, validações, tratamento de registros e organização dos relacionamentos. |
| **Gold** | Consolida informações por meio de agregações SQL, `JOIN` e `GROUP BY`, facilitando as análises. |

### 2.1. Raw — Dados originais

São utilizadas quatro tabelas para armazenar os arquivos de origem:

- `raw_viagem`
- `raw_pagamento`
- `raw_passagem`
- `raw_trecho`

As colunas são armazenadas como `VARCHAR`, preservando os dados recebidos antes do tratamento.

### 2.2. Silver — Dados tratados

Os dados são convertidos para tipos adequados, como `DATE`, `DECIMAL` e `INTEGER`.

As tabelas possuem chaves primárias, relacionamentos por chaves estrangeiras e restrições adicionais de integridade.

Também são calculados:

- **Valor total da viagem:** diárias + passagens + outros gastos − devoluções.
- **Duração da viagem:** diferença entre a data final e a inicial, considerando os dois dias.

Registros que não atendem às validações são rejeitados durante a transformação, com registro de informações no log.

### 2.3. Gold — Dados agregados

A camada Gold utiliza consultas com `JOIN` e `GROUP BY` para consolidar informações de pagamentos e trechos.

São criadas tabelas físicas e views para apoiar as consultas analíticas.

## 3. Perguntas de negócio

O projeto busca responder às seguintes questões:

1. Quais são os cinco órgãos superiores com maior custo total em viagens?
2. Quais são os três destinos com maior custo médio por viagem?
3. Qual foi a viagem de maior duração e qual foi seu custo?
4. Qual tipo de pagamento apresenta o maior valor médio?
5. Qual meio de transporte é mais utilizado nos trechos?
6. Qual UF de destino aparece com maior frequência nos trechos?
7. Qual órgão pagador realizou o maior volume de pagamentos?

As análises são desenvolvidas em SQL e apresentadas em tabelas e gráficos no notebook.

## 4. Tecnologias utilizadas

- **Python:** desenvolvimento do processo ETL e tratamento dos dados.
- **PostgreSQL:** armazenamento e gerenciamento do banco de dados.
- **SQL:** criação das tabelas, relacionamentos e consultas analíticas.
- **Pandas:** leitura e manipulação dos arquivos CSV.
- **Matplotlib:** criação de visualizações gráficas.
- **SQLAlchemy:** integração entre Python e PostgreSQL.
- **Psycopg2:** conexão e operações com o banco PostgreSQL.
- **Git e GitHub:** versionamento e organização do desenvolvimento.

## 5. Estrutura do repositório

```text
Analise-de-Dados-Projeto-Avaliativo-M1/
│
├── SQL/
│   └── 0_criar_banco.sql
│
├── SCRIPTS/
│   ├── config.py
│   ├── banco.py
│   ├── 1_extrair.py
│   └── 2_transformar.py
│
├── NOTEBOOKS/
│   └── 3_analise.ipynb
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 6. Instruções de execução

### 6.1. Pré-requisitos

- Python 3.10 ou superior.
- PostgreSQL.
- Git.

### 6.2. Clonar o repositório

```bash
git clone https://github.com/KrathK9722/Analise-de-Dados-Projeto-Avaliativo-M1.git

cd Analise-de-Dados-Projeto-Avaliativo-M1
```

### 6.3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6.4. Configurar as variáveis de ambiente

Crie uma cópia do arquivo `.env.example` com o nome `.env` e configure os dados de acesso ao PostgreSQL.

Exemplo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=viagens_db
DB_USER=projeto_user
DB_PASSWORD=sua_senha
DRIVE_FILE_ID=
```

O arquivo `.env` contém informações privadas e não deve ser enviado ao GitHub.

### 6.5. Criar o banco de dados

Execute o arquivo:

```text
SQL/0_criar_banco.sql
```

Ele contém a estrutura das tabelas Raw e Silver.

### 6.6. Executar a extração

```bash
python SCRIPTS/1_extrair.py
```

O script realiza o download dos dados, lê os arquivos CSV em blocos e carrega os registros nas tabelas Raw.

### 6.7. Executar a transformação

```bash
python SCRIPTS/2_transformar.py
```

O processo transforma os dados da camada Raw para Silver, realizando conversões e validações.

### 6.8. Executar as análises

Abra o notebook:

```text
NOTEBOOKS/3_analise.ipynb
```

Execute as células para gerar as tabelas, consultas e visualizações da camada Gold.

## 7. Regras de negócio

- Os valores monetários são convertidos para formato decimal.
- As datas são convertidas para o tipo `DATE`.
- A duração da viagem considera a data inicial e a final.
- Os destinos são identificados a partir das informações de cidade e UF presentes nos trechos.
- Uma viagem com mais de um destino pode participar de mais de um grupo na análise de custo médio por destino.
- Os custos por órgão superior são calculados a partir dos valores registrados nas viagens.
- Os totais por órgão pagador são calculados a partir dos registros da tabela de pagamentos.
- A camada Raw preserva os dados originais, enquanto os registros inválidos são tratados durante a transformação.

## 8. Segurança e versionamento

O projeto utiliza variáveis de ambiente para armazenar credenciais de acesso ao banco de dados.

O `.gitignore` evita o versionamento de arquivos privados, arquivos CSV, arquivos ZIP e diretórios temporários.

O desenvolvimento é organizado em branches por funcionalidade, com commits específicos para cada etapa.

## 9. Limitações e melhorias futuras

- Implementar testes automatizados para validar as transformações e os relacionamentos.
- Aprimorar o monitoramento dos registros rejeitados durante o ETL.
- Comparar sistematicamente as quantidades e os valores entre as camadas.
- Implementar estratégias de carga mais eficientes para grandes volumes de dados.
- Expandir as análises com novos indicadores e visualizações.

## 10. Conclusão

O projeto aplica conceitos de extração, transformação e análise de dados em uma situação prática, utilizando dados públicos e ferramentas amplamente utilizadas na área de dados.

A separação em camadas permite organizar o processamento, preservar os dados de origem e disponibilizar informações tratadas para consultas e análises de negócio.

Os resultados e as conclusões específicas das sete perguntas devem ser registrados após a execução do notebook com os dados reais.
