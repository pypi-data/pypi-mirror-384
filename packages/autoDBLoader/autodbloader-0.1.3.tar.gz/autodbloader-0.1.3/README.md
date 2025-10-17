# AutoDBLoader

**AutoDBLoader** é uma biblioteca Python para automatizar o processo de extração e inserção de dados em bancos relacionais a partir de arquivos **CSV**, **Parquet** ou **JSON**, preservando a integridade referencial e respeitando relacionamentos entre tabelas.


## 📌 Para que serve


A biblioteca foi desenvolvida para facilitar **extração** e **migração** de dados entre bancos de dados relacionais, garantindo que:

- Os dados sejam inseridos na ordem correta, respeitando as **chaves estrangeiras**;
- Colunas únicas e relacionamentos sejam **validados antes da inserção**;
- Dados sejam carregados em **batches** para otimizar performance e uso de memória;
- Os dados sejam extraídos e armazenados em **arquivos separados por tabela**;
- **Logs de progresso** sejam mantidos para permitir retomada segura em caso de falhas.



## 🚀 Instalação e Utilização


- No terminal, execute:
    - `pip install autodbloader`

- Após a instalação, execute `autodbloader` no terminal. Isso iniciará uma interface de configuração, onde é possível:
    - Configurar a conexão com o banco de dados
    - Definir métodos de extração ou inserção de dados
    - Preencher os formulários de configuração referentes às tabelas do banco

- Depois de preencher todos os campos, é possível gerar o JSON de configuração. A partir daí, há duas opções:
    - Executar diretamente pela interface e acompanhar os logs de execução no terminal
    - Copiar o JSON e utilizá-lo em um arquivo Python, instanciando a biblioteca e chamando o método desejado com a configuração criada


### 🧩 Executar a interface via script

Agora é possível abrir a interface gráfica do AutoDBLoader diretamente por um script Python.  
Isso permite utilizá-la sem precisar do terminal.

Exemplo de uso:
```python
import autoDBLoader

autoDBLoader.run_interface()
```


## ⚙️ Como funciona

A biblioteca opera em três etapas principais:

1. **Validação**  
   - Verifica a estrutura do dicionário de configuração;
   - Confere a existência dos arquivos e tabelas;
   - Valida a compatibilidade de tipos entre arquivo e banco;
   - Checa permissões de acesso ao banco;
   - Confere diretórios e arquivos existentes;
   - Valida a execução de queries personalizadas.

2. **Extração**  
   - Executa queries padrão ou personalizadas;
   - Extrai os dados do banco de dados;
   - Salva no diretório e formato informado (**CSV**, **Parquet** ou **JSON**).

3. **Inserção ordenada**  
   - Insere os dados respeitando os relacionamentos;
   - Adiciona colunas temporárias para controle dos antigos IDs;
   - Executa inserção em lotes para maior performance;
   - Mantém logs para garantir continuidade em caso de falhas.

## 📋 Requisitos e configurações obrigatórias:

### Processo de **inserção**:

- O banco de dados **já deve estar criado** com a estrutura das tabelas necessárias.
- O usuário da conexão precisa ter **permissão** para criar, alterar e deletar tabelas (criação de colunas, alteração, inserção e exclusão).
- **SGBDs suportados**:
  - MySQL
  - PostgreSQL
  - Oracle


Para que o **processo de inserção** funcione corretamente, os arquivos de dados devem atender aos seguintes critérios:

- Cada arquivo representa **uma tabela** do banco de dados.
- Os nomes das colunas no arquivo devem **corresponder exatamente aos nomes dos atributos** da tabela no banco.
- Os arquivos **devem conter todas as chaves primárias** dos registros.
- As **chaves estrangeiras** também devem estar presentes e corretas para garantir a integridade referencial.
- Os arquivos devem estar **completos e consistentes** com a estrutura da tabela, incluindo tipos de dados compatíveis.
- Os arquivos devem estar no formato informado no **JSON de configuração** e podem ser:
  - CSV (com separador configurável)
  - Parquet
  - JSON (newline-delimited)
- Os arquivos podem conter **atributos extras**, que serão descartados conforme especificado no campo **unwanted_attributes** no JSON de configuração.

> ⚠️ Observação: O AutoDBLoader não cria nem adivinha chaves primárias ou estrangeiras. Se algum valor estiver faltando ou incorreto, a inserção pode falhar ou gerar inconsistências no banco.

### Processo de **extração**:

- O usuário da conexão precisa ter **permissão** para executar **executar consultas SQL simples** (ex.: `SELECT * FROM tabela`).
- **SGBDs suportados**:
  - MySQL
  - PostgreSQL
  - Oracle
- Os dados de cada tabela serão salvos **em arquivos separados**, onde cada arquivo contém unicamente os dados de uma tabela.
- Os arquivos serão salvos no formato informado no **JSON de configuração**, que pode ser:
  - CSV (com separador configurável)
  - Parquet
  - JSON (newline-delimited)
- A extração pode utilizar uma **consultas SQL personalizada**, que deve ser **informada** no **JSON de configuração** e cujo resultado será salvo no arquivo da tabela.


## 📂 Sistema de Logs e Retomada


O **AutoDBLoader** possui um sistema de logs que garante a **continuidade do processo** em caso de falhas, registrando quais tabelas já foram processadas.

- **Inserção de dados**
  - O log é salvo em uma **tabela no banco de dados** chamada `log_autodbloader`.
  - Esta tabela **só é criada se ocorrer um erro** durante o processo de inserção.
  - Ela registra quais tabelas já foram inseridas, permitindo que a próxima execução **retome de onde parou**.

- **Extração de dados**
  - O log é salvo em um **arquivo JSON** chamado `log_tables_extract.json`.
  - Ele armazena as tabelas que já foram extraídas.
  - Na próxima execução, o AutoDBLoader verifica esse arquivo e **retoma apenas as tabelas que ainda não foram extraídas**.

> ⚠️ Observação: Manter o arquivo `log_tables_extract.json` ou a tabela `log_autodbloader` é importante para garantir que o processo seja retomado corretamente após falhas.


## 📄 Formato do JSON de configuração

O processo é orientado por um **JSON de configuração** contendo:

### a) Configuração de conexão ao banco
- `hostname`: Host de conexão ao banco.
- `username`: Usuário de conexão.
- `password`: Senha do usuário.
- `database`: Banco de dados que será utilizado.
- `port`: Porta de acesso ao banco.
- `sgbd`: Sistema gerenciador de banco de dados (**mysql**, **postgre**, **oracle**, em letras minúsculas).

### b) Configuração de tabelas (inserção)
- `name_table`: Nome da tabela.
- `path_file`: Caminho do arquivo que contém os dados da tabela.
- `type_file`: Tipo do arquivo (**csv**, **parquet**, **json**, em letras minúsculas).
- `file_sep`: Usado apenas para arquivos CSV. Informa o caractere separador (ex.: `","` ou `";"`)
- `unwanted_attributes`: Lista de atributos que devem ser ignorados.

### c) Configuração de tabelas (extração)
- `name_table`: Nome da tabela.
- `query`: Consultas SQL personalizada para extrair os dados.   
    - Deve conter uma consulta SQL válida.  
    - Se não for necessária, utilize `"query": ""`.  
- `type_file`: Tipo do arquivo (**csv**, **parquet**, **json**, em letras minúsculas).
- `file_sep`: Usado apenas para arquivos CSV. Informa o caractere separador (ex.: `","` ou `";"`)

### d) Configuração adicional para extração
- `path`: Diretório onde os arquivos extraídos serão salvos.

---

### 📌 Exemplo simplificado de configuração para inserção de dados:

```json
{
    "db":{
        "hostname":"localhost",
        "username":"root",
        "password":"admin",
        "database":"fraud_analysis",
        "port":3306,
        "sgbd":"mysql"
        },
    "tables":[
        {
            "name_table":"users",
            "path_file":"C:/user/dados/users_data.csv",
            "type_file":"csv",
            "unwanted_attributes":["use_cpf", "use_password"],
            "file_sep":","
        },
        {
            "name_table":"cards",
            "path_file":"C:/user/dados/cards_data.parquet",
            "type_file":"parquet",
            "unwanted_attributes":[]
        },
        {
            "name_table":"transactions",
            "path_file":"C:/user/dados/transactions_data.json",
            "type_file":"json",
            "unwanted_attributes":[],
        },
        {
            "name_table":"mcc",
            "path_file":"C:/user/dados/mcc_codes.csv",
            "type_file":"csv",
            "unwanted_attributes":[],
            "file_sep":";"
        }
    ]
}
```

#### 📝 Exemplo de inserção utilizando Python:
```python
    from autoDBLoader import insert_date

    config  =  {"db":{ ... },
                "tables":{ ... }}
    insert_date(config)

```

### 📌 Exemplo simplificado de configuração para extração de dados:

```json
{
    "db":{
        "hostname":"localhost",
        "username":"root",
        "password":"admin",
        "database":"fraud_analysis",
        "port":3306,
        "sgbd":"mysql"
        },
    "path": "C:/user/dados/",
    "tables":[
        {
            "name_table":"users",
            "type_file":"csv",
            "query":"SELECT use_id, use_name, use_age, use_address from fraud_analysis.users
                     WHERE use_age >= 18",
            "file_sep":","
        },
        {
            "name_table":"cards",
            "type_file":"parquet",
            "query":"",
        },
        {
            "name_table":"transactions",
            "type_file":"json",
            "query":"",
        },
        {
            "name_table":"mcc",
            "type_file":"csv",
            "query":"",
            "file_sep":";"
        }
    ]
}
```

#### 📝 Exemplo de extração utilizando Python:
```python
    from autoDBLoader import extract_date

    config  =  {"db":{ ... },
                "path": "C:/user/dados",
                "tables":{ ... }}
    extract_date(config)

```


