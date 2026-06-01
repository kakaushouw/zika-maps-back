# ==============================================================================
# Dockerfile Otimizado para Produção (VPS) - ZikaMaps API
# ==============================================================================

# Estágio 1: Compilação e preparação de dependências
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar pacotes de sistema necessários para compilar dependências se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de dependências e instalar na pasta /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Estágio 2: Imagem de execução final e leve
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production

# Instalar apenas as bibliotecas runtime necessárias (ex: libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências pré-instaladas do builder
COPY --from=builder /install /usr/local

# Copiar todo o código-fonte da aplicação
COPY . .

# Criar e configurar um usuário não-root por questões de segurança (VPS Hardening)
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Expor a porta em que a aplicação vai rodar
EXPOSE 5000

# Comando de inicialização com Uvicorn rodando 4 workers para concorrência em produção
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
