# 🛍️ Microsserviço Catalog - Ateliê Digital

## 📖 Sobre o Projeto
O **Ateliê Digital** é um sistema web que funciona como um marketplace exclusivo para produtos artesanais. O objetivo da plataforma é conectar diretamente os artesãos independentes aos consumidores, oferecendo ferramentas para que os vendedores gerenciem seus negócios e os clientes encontrem produtos com facilidade e segurança.

Neste repositório encontra-se o microsserviço de **Catalog (Catálogo)**. Dentro da arquitetura do ecossistema, ele é a API responsável por gerenciar toda a vitrine de produtos artesanais, os perfis e endereços das lojas dos artesãos, além das funcionalidades de busca e categorização.

Apesar de rodar de forma independente, este microsserviço se comunica e integra ativamente com os demais serviços da arquitetura — enviando dados críticos sobre os produtos e lojas para o *Orders* e disparando eventos de alterações (como atualização de estoque, preços, exclusão lógica de produtos e dados de endereços) via mensageria assíncrona para o microsserviço de *Auditoria de Logs*.

## 🚀 Tecnologias e Recursos
Este microsserviço foi construído utilizando as seguintes tecnologias:

* **FastAPI:** Framework principal, moderno e assíncrono para a construção ágil da API (Python 3.12+).
* **FastStream com RabbitMQ:** Framework moderno e ultrarrápido para mensageria assíncrona, responsável por publicar e consumir os eventos nas filas do RabbitMQ sem bloquear a thread principal.
* **PostgreSQL:** Banco de dados relacional (Produção/Dev) para armazenar com segurança as informações de produtos, categorias e lojas.
* **SQLAlchemy 2.0+:** ORM moderno para modelagem e mapeamento objeto-relacional assíncrono.
* **Alembic:** Ferramenta robusta para gerenciamento de migrações e versionamento do banco de dados.
* **RabbitMQ:** Mensageria utilizada para comunicação assíncrona orientada a eventos dentro do ecossistema.
* **Ferramentas de Suporte:**
    * **uv:** Gerenciador de pacotes e ambientes virtuais ultrarrápido.
    * **Pytest & Testcontainers:** Para criação e execução de testes unitários e de integração utilizando um banco Postgres real isolado automaticamente via container.
    * **Ruff:** Linter e formatador de código para manter os padrões de qualidade e estilo.
    * **Taskipy:** Executor de tarefas para facilitar e padronizar o uso de comandos no terminal.

---

## ⚙️ Configuração do Ambiente

Para rodar este projeto, utilizaremos o **uv** para gerenciar o ambiente, as bibliotecas e sincronizar as dependências.

### 1. Instalação do uv
Se você ainda não tem o `uv` instalado, abra o seu terminal e execute o comando correspondente ao seu sistema operacional:

**No Linux (ou macOS):**
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

### 2. Criando o Ambiente Virtual
Na pasta raiz do projeto, crie um ambiente virtual limpo executando:
```bash
uv venv
```

Após a criação, **ative o ambiente virtual**:
* **Linux / macOS:**
    ```bash
    source .venv/bin/activate
    ```
* **Windows:**
    ```cmd
    .venv\Scripts\activate

### 3. Instalando as Bibliotecas
Com o ambiente ativado, instale as dependências listadas nas tecnologias utilizando o `uv`. Você pode instalar todas de uma vez através do seu arquivo de dependências (como o `pyproject.toml` ou `requirements.txt`):

```bash
uv pip install -r requirements.txt
```

*Caso precise instalar as bibliotecas manualmente para testar o ambiente, o comando base seria:*
```bash
uv pip install fastapi uvicorn psycopg2-binary sqlalchemy python-jose[cryptography] pika pytest ruff taskipy faststream[cli, rabbit] alembic pwdlib[argon2]
```
---

## ▶️ Como Executar a API

Você pode rodar o serviço em modo local de desenvolvimento diretamente via terminal ou de forma conteinerizada utilizando o Docker Compose para emular o ecossistema completo do Ateliê Digital.

### Opção 1: Execução Local com Taskipy

Como o projeto utiliza o **Taskipy**, as rotinas de execução estão simplificadas. Para iniciar o servidor local de desenvolvimento, basta rodar:

```bash
task run
```

*(Se não tiver os scripts do taskipy configurados, você pode iniciar o servidor padrão do FastAPI rodando `fastapi dev` ou `uvicorn main:app --reload --port 8008`)*.

### Opção 2: Execução via Docker Compose (Recomendado)
Para integrar o serviço de orders aos demais microsserviços do **Ateliê Digital** (como o RabbitMQ e o banco de dados PostgreSQL), a execução via Docker Compose garante que todos os containers compartilhem a mesma rede de comunicação interna.

1. **Crie a rede de comunicação global do projeto** (caso ainda não tenha sido criada no seu ambiente docker):
   ```bash
   docker network create atelie-network
   ```

2. **Inicie o serviço construindo a imagem do container**:
   Na raiz do repositório, execute o comando abaixo para realizar o build da imagem Docker e subir o serviço em background ou anexado ao terminal:
   ```bash
   docker compose up --build
   ```

Com o container em execução, o serviço começará automaticamente a escutar os eventos do RabbitMQ na rede `atelie-network` e o painel administrativo estará acessível no navegador através de `http://localhost:8000/` (ou na porta configurada em seu `docker-compose.yml`).

## 🧪 Testes e Qualidade
O microsserviço preza por um alto rigor em qualidade de software. Os testes automatizados utilizam a biblioteca Testcontainers, o que significa que durante a execução uma instância temporária e real do PostgreSQL é levantada em um container isolado para executar a suíte de testes de integração sem poluir seu banco de dados local ou de desenvolvimento.

Executar todos os testes e ver cobertura:

```Bash
task test
```
- Verificar Lint e Formatação:

```Bash
task lint
```

## 📁 Estrutura de Comandos (Taskipy)

Para gerenciar o ciclo de desenvolvimento, verificação e automação de containers, utilize os atalhos configurados com o Taskipy:

`task run`: Inicia o servidor de desenvolvimento.

`task test`: Executa os testes unitários e de integração com cobertura.

`task lint`: Verifica padrões de código com Ruff.

`task format`: Aplica formatação automática de código.

`task up`: Sobe os containers Docker.

`task down`: Derruba os containers Docker.

`task restart`: Reinicia o container da API.

`task rebuild`: Rebuilda e sobe os containers.

`task logs`: Acompanha os logs da API em tempo real.
