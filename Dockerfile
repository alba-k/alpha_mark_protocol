# ==========================================
# ETAPA 1: BUILDER (El Constructor)
# ==========================================
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalar herramientas de compilación de forma robusta
RUN apt-get update --fix-missing
RUN apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# ETAPA 2: RUNNER (El Ejecutor)
# Imagen final ligera y segura
# ==========================================
FROM python:3.11-slim as runner

# ⭐ ELIMINADAS: Las líneas de 'useradd akmuser'
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar el código fuente (se elimina el --chown)
COPY . .

# ⭐ ELIMINADA: La línea 'USER akmuser'

EXPOSE 8000 5000

# Arranca la API/Web para transacciones manuales
CMD ["python", "-m", "akm.interface.api.server"]