# Ateliê Digital - Catalog Service
- Este é o microsserviço de Catálogo do ecossistema Ateliê Digital. Ele gerencia a vitrine de produtos, os perfis das lojas dos artesãos, buscas e categorias.

## 🚀 Tecnologias e Stack
- Linguagem: Python 3.12+
- Gestor de Pacotes: uv
- Web Framework: FastAPI (Assíncrono)
- Banco de Dados: PostgreSQL (Produção/Dev)
- ORM: SQLAlchemy 2.0+
- Migrações: Alembic
- Containerização: Docker & Docker Compose
- Qualidade de Código: Ruff (Lint & Formatação)
- Task Runner: Taskipy
- Testes: Pytest & Testcontainers (Postgres isolado para testes)

## 🛠️ Como Executar o Projeto
**1. Configurar Variáveis de Ambiente**
```bash
cp .env.example .env
```
- (Certifique-se de que a DATABASE_URL aponta para o Postgres no Docker)

**2. Executar com Docker (Recomendado)**
- Para subir a API e o Banco de Dados:

```Bash
docker compose up --build
```

- após o primeiro build
```bash
docker compose up
```
- A API estará disponível em http://localhost:8000.

**3. Executar Localmente (Desenvolvimento)**
- Se preferir rodar apenas o banco no Docker e a API no seu terminal:
```Bash
uv sync
task run
```
### 🧪 Testes e Qualidade
- Os testes utilizam Testcontainers, o que significa que um banco Postgres real é levantado automaticamente dentro de um container apenas para a execução dos testes, garantindo isolamento total.

- Executar todos os testes e ver cobertura:

```Bash
task test
```
- Verificar Lint e Formatação:

```Bash
task lint
```
### 📁 Estrutura de Comandos (Taskipy)
```task run ```: Inicia o servidor de desenvolvimento.

```task test```: Executa os testes unitários e de integração com cobertura.

```task lint ```: Verifica padrões de código com Ruff.

```task format ```: Aplica formatação automática de código.