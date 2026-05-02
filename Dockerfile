FROM python:3.12-slim

# Instala o uv dentro do container (forma oficial e rápida)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copia os arquivos de configuração 
COPY pyproject.toml uv.lock ./

# Instala as dependências no sistema do container usando o uv
# O uv lê o seu pyproject.toml e o uv.lock automaticamente
# Removida a flag --frozen que causou o erro
RUN uv pip install --system --no-cache -r pyproject.toml

# Copia o restante do projeto
COPY . .

# Permissão para o script de entrada
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]