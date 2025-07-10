# Projeto de Coleta e Análise de Dados do Airbnb

Este projeto de engenharia de dados tem como objetivo demonstrar um fluxo completo de extração, tratamento e carga (ETL) de dados de anúncios da plataforma Airbnb. Utilizando técnicas de Web Scraping, os scripts e notebooks coletam, processam e armazenam informações de imóveis, preparando-os para análises futuras.

## Como Funciona o Projeto

O projeto é dividido em três fases principais, cada uma representada por um módulo ou script específico:

1.  **Extração em Massa de Anúncios**: O primeiro passo consiste em simular buscas de um usuário no Airbnb para coletar informações gerais de múltiplos anúncios.
2.  **Extração de Detalhes dos Imóveis**: Com a lista de anúncios em mãos, o segundo passo é visitar a página individual de cada um para extrair informações detalhadas.
3.  **Tratamento e Carga (ETL)**: A fase final envolve limpar, transformar e normalizar os dados brutos, carregando-os em um banco de dados PostgreSQL para futuras análises.

## Estrutura do Projeto

O projeto é composto por notebooks Jupyter e scripts Python, cada um com uma função específica dentro do fluxo de trabalho.

### Notebooks

  * **`notebook/1 - exemplo_script_extracao_anuncios.ipynb`**: Este notebook é o ponto de partida do projeto. Ele demonstra como funciona a extração em massa de dados das páginas de busca do Airbnb. Ele simula um usuário pesquisando por diferentes locais e datas, navegando por todas as páginas de resultados e salvando as informações básicas de cada anúncio (ID, título, preço, etc.) em um arquivo CSV.

  * **`notebook/2 - exemplo_extracao_detalhes_imoveis.ipynb`**: Após a coleta inicial, este notebook demonstra como o script utiliza o arquivo CSV gerado anteriormente para visitar o link de cada anúncio individualmente. Seu objetivo é extrair detalhes que não estão disponíveis na página de busca, como o número de quartos, camas, banheiros e as regras de check-in/checkout.

  * **`notebook/3 - tratamento_e_insercao_dos_dados.ipynb`**: Este é o notebook de ETL (Extração, Transformação e Carga). Ele carrega o dataset completo e "plano", limpa os dados e os normaliza em várias tabelas menores e relacionadas (como `cidade`, `bairro`, `imovel`). Em seguida, ele insere esses dados tratados em um banco de dados PostgreSQL.

  * **`notebook/4 - explicacao_banco_de_dados.ipynb`**: Este notebook não executa um processo, mas serve como a documentação de um módulo de funções reutilizáveis (`banco_de_dados.py`). Ele explica como o projeto centraliza a lógica de comunicação com o banco de dados para abrir e fechar conexões de forma segura, inserir dados em massa e executar outras operações de forma eficiente.

### Scripts

  * **`scripts/1 - script_extracao_dados_pagina_principal_airbnb.py`**: A versão em script do primeiro notebook, projetada para ser executada de forma automatizada. Realiza a busca em massa e salva os dados de forma incremental para otimizar o uso de memória.

  * **`scripts/2 - script extracao_paginas_individuais_imoveis.py`**: A versão em script do segundo notebook. Visita cada link de anúncio para extrair detalhes e implementa uma lógica para retomar o trabalho de onde parou, além de reiniciar o navegador periodicamente para garantir a estabilidade.

  * **`scripts/3 - tentativa_web_scrappling_paralelo.py`**: Uma versão mais avançada do script de extração de detalhes, que utiliza múltiplos processos para executar a tarefa em paralelo. Isso acelera significativamente a coleta de dados, dividindo a carga de trabalho entre vários "workers".

### Módulos de Funções

  * **`funcoes/banco_de_dados.py`**: Este módulo Python centraliza todas as funções para interagir com o banco de dados PostgreSQL. Ele oferece funções para abrir e fechar conexões, ler tabelas, inserir dados em massa com o comando `COPY` para alta performance, e excluir e atualizar registros em lote.

## Como Configurar e Rodar o Ambiente

Siga os passos abaixo para configurar e executar o projeto:

### 1\. Pré-requisitos

  * Python 3.x instalado.
  * Um banco de dados PostgreSQL em execução.

### 2\. Instalação das Dependências

Todas as bibliotecas Python necessárias estão listadas no arquivo `requirements.txt`. Para instalá-las, execute o seguinte comando no seu terminal:

```bash
pip install -r requirements.txt
```

### 3\. Configuração do Banco de Dados

Antes de executar os scripts, é necessário configurar a conexão com o banco de dados. Abra o arquivo `funcoes/banco_de_dados.py` e altere as credenciais na função `abre_conexao_banco_de_dados` para corresponder à sua configuração do PostgreSQL:

```python
def abre_conexao_banco_de_dados():
    try:
        conn = psycopg2.connect(
            host="SEU_HOST",
            database="SEU_BANCO",
            user="SEU_USUARIO",
            password="SUA_SENHA",
            port=SUA_PORTA
        )
        # ...
```

### 4\. Execução do Projeto

Para executar o projeto, siga a ordem dos scripts/notebooks:

1.  **Extração de Anúncios**: Execute o primeiro script para iniciar a coleta de dados gerais.

    ```bash
    python "scripts/1 - script_extracao_dados_pagina_principal_airbnb.py"
    ```

    Isso gerará um arquivo CSV com os dados brutos.

2.  **Extração de Detalhes**: Em seguida, execute o segundo script, passando o nome do arquivo gerado no passo anterior como argumento.

    ```bash
    python "scripts/2 - script extracao_paginas_individuais_imoveis.py" "nome_do_arquivo_gerado.csv"
    ```

    Para uma execução mais rápida em paralelo (requer mais recursos de CPU), você pode usar o script de extração paralela:

    ```bash
    python "scripts/3 - tentativa_web_scrappling_paralelo.py" "nome_do_arquivo_gerado.csv" <numero_de_threads>
    ```

3.  **Tratamento e Carga (ETL)**: Por fim, execute o notebook `3 - tratamento_e_insercao_dos_dados.ipynb` para limpar, normalizar e carregar os dados no banco de dados. Certifique-se de que o caminho do arquivo de entrada no notebook está correto.