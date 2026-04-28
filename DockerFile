FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (temporárias)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (cache)
COPY requirements.txt .

# Instala dependências Python (incluindo gunicorn)
RUN pip install --no-cache-dir -r requirements.txt

# Cria usuário não-root
RUN useradd -m appuser

# Copia código
COPY . .

# Ajusta permissões
RUN chown -R appuser:appuser /app

# Troca para usuário não-root
USER appuser

# Avisa que a aplicação vai se comunicar pela porta 8000
EXPOSE 8000

# O comando exato que liga o servidor Django quando o container iniciar


# Comando
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "platacursos.wsgi:application"]