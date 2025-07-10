# PlanB - Planejador de Viagens Inteligente

O PlanB é uma aplicação web desenvolvida com Django, projetada para ajudar usuários a planejar suas viagens de forma inteligente. A ferramenta permite buscar, comparar e encontrar as melhores opções de hospedagem, analisando preços, tendências e disponibilidade em diferentes localidades.

## Como Executar o Projeto

Você pode executar o projeto de duas maneiras: localmente com um ambiente Python ou utilizando Docker para uma configuração conteinerizada.

### 0\. Configurando o Banco de Dados com Docker (Obrigatório)

Antes de rodar a aplicação Django, o banco de dados PostgreSQL deve ser iniciado via Docker. Esta etapa é necessária para os dois modos de execução.

#### Pré-requisitos

  * Docker
  * Docker Compose

#### Passos

1.  **Estrutura de Pastas:**
    Na raiz do seu projeto, crie uma pasta chamada `banco_de_dados` e coloque os arquivos `docker-compose.yml`, `postgresql.conf` e `pg_hba.conf` dentro dela.

2.  **Verifique a Configuração do `docker-compose.yml`:**
    Este arquivo define o serviço do PostgreSQL. As credenciais e a porta mapeada aqui serão usadas para conectar a aplicação ao banco.

    **Arquivo: `banco_de_dados/docker-compose.yml`**

    ```yaml
    services:
      postgres:
        image: postgres:16
        container_name: planb_DB
        environment:
          POSTGRES_USER: usuario      # <-- Usuário do banco
          POSTGRES_PASSWORD: senha  # <-- Senha do banco
          POSTGRES_DB: planb          # <-- Nome do banco
        volumes:
          - ./data:/var/lib/postgresql/data
          - ./:/etc/postgresql # Mapeia os arquivos .conf

        ports:
          - "5436:5432"             # <-- Porta externa
        restart: always
    ```

3.  **Inicie o Contêiner do Banco de Dados:**
    Navegue até o diretório `banco_de_dados` e execute o comando:

    ```bash
    cd banco_de_dados
    docker compose up -d
    ```

    O seu banco de dados agora está rodando e acessível na porta `5436` do seu computador.

-----

### 1\. Execução Local (Ambiente Python)

Siga os passos abaixo para rodar o projeto diretamente em sua máquina.

#### Passos

1.  **Clone o Repositório e Navegue até a Pasta:**

    ```bash
    git clone https://github.com/macheuz/sistema_airbnb_laboratorio/tree/master
    cd planejador_airbnb
    ```

2.  **Crie e Ative um Ambiente Virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as Dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a Conexão com o Banco de Dados:**
    As configurações (`settings.py`) leem as credenciais de um arquivo `.env`. Crie um arquivo chamado `.env` na raiz do projeto (`planejador_airbnb/.env`) e preencha-o com os dados do contêiner do banco de dados que você iniciou na Etapa 0.

    **Arquivo: `.env` (crie este arquivo)**

    ```ini
    DJANGO_ENV=prod  # -> define o ambiente como producao
    ```

5.  **Aplique as Migrações e Inicie o Servidor:**

    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

    A aplicação estará disponível em `http://127.0.0.1:8000`.

-----

### 2\. Execução com Docker

Para uma execução de produção isolada e portável.

#### Passos e Configurações

1.  **Ajuste o `settings_prod.py`:**

      * **`ALLOWED_HOSTS`**: Adicione seu domínio para permitir que o Django o acesse.
      * **`DATABASES`**: Altere o `HOST` para `host.docker.internal`. Este é um endereço especial do Docker que permite ao contêiner da aplicação se conectar a um serviço (nosso banco de dados) que está rodando na máquina hospedeira (host).

    **Arquivo: `planejador_airbnb/settings_prod.py`**

    ```python
    # ... (outras configurações)

    ALLOWED_HOSTS = [
        "seu-dominio.com",      # <-- ALTERAR AQUI
        "www.seu-dominio.com",  # <-- ALTERAR AQUI
    ]

    # ... (outras configurações)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'planb',
            'USER': 'usuario',
            'PASSWORD': 'senha',
            'HOST': 'host.docker.internal', # <-- ALTERAR AQUI
            'PORT': '5436',
        }
    }

    # ... (outras configurações)
    ```

2.  **Configure o Nginx (`default.conf`):**
    Este arquivo é o proxy reverso. Altere o `server_name` e os caminhos do certificado SSL para corresponderem ao seu domínio.

    **Arquivo: `planejador_airbnb/nginx/conf/default.conf`**

    ```nginx
    # ...

    server {
        listen 80;
        server_name seu-dominio.com; # <-- ALTERAR AQUI

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name seu-dominio.com; # <-- ALTERAR AQUI

        ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem; # <-- ALTERAR AQUI
        ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem; # <-- ALTERAR AQUI
        include /etc/letsencrypt/options-ssl-nginx.conf;
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ...
    ```

3.  **Configure o Script do Certificado SSL (`init-letsencrypt.sh`):**
    Este script gera o certificado. Atualize as variáveis `domains` e `email`.

    **Arquivo: `planejador_airbnb/init-letsencrypt.sh`**

    ```bash
    #!/bin/bash

    # ...

    domains=(seu-dominio.com) # <-- ALTERAR AQUI
    email="seu-email@seu-dominio.com" # <-- ALTERAR AQUI (Opcional, mas recomendado)

    # ...
    ```

4.  **Inicie os Contêineres da Aplicação:**
    Na raiz do projeto `planejador_airbnb`, execute:

    ```bash
    docker compose up -d --build
    ```

5.  **Gere o Certificado SSL (Apenas na primeira vez):**
    Execute o script para obter o certificado.

    ```bash
    # Dê permissão de execução ao script
    chmod +x init-letsencrypt.sh

    # Execute o script
    ./init-letsencrypt.sh
    ```

Sua aplicação estará disponível em `https://seu-dominio.com`.
Lembre-se de apontar seu domínio para seu servidor.
Você pode carregar os dados para o banco de dados seguindo o passo a passo de scrappling, no script 3 (leia o readme.md do scrappling)