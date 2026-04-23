# Ateliê Digital - Catalog Service 

Este é o microsserviço de **Catálogo** do ecossistema Ateliê Digital. Ele gere a montra de produtos, os perfis das lojas dos artesãos, as buscas e as avaliações.

## 🚀 Tecnologias e Stack
- **Linguagem:** Python 3.12+
- **Gestor de Pacotes:** [uv](https://github.com/astral-sh/uv)
- **Web Framework:** FastAPI (Assíncrono)
- **Banco de Dados:** SQLite com `aiosqlite`
- **ORM:** SQLAlchemy 
- **Qualidade de Código:** Ruff (Lint & Formatação)
- **Task Runner:** Taskipy
- **Testes:** Pytest

### Configurar Ambiente:
```bash
cp .env.example .env
```

### Executar:
```
task run
```
