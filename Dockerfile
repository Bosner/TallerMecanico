# Usa bookworm-slim como base (compatible con Railway)
FROM python:3.11-slim-bookworm

# Instala TODAS las dependencias necesarias ANTES de wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libfontconfig1 \
    libxrender1 \
    libjpeg62-turbo \
    libssl3 \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Descarga la versión correcta para bookworm (0.12.6.1-3 es estable)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -O wkhtmltox.deb \
    && dpkg -i wkhtmltox.deb || true \
    && apt-get install -f -y \
    && rm wkhtmltox.deb

# Link explícito al binario (a veces no se agrega al PATH automáticamente)
RUN ln -s /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf

# Verifica instalación (ahora debería funcionar)
RUN wkhtmltopdf --version

# Configura app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

# Comando de inicio: migraciones + app (ajusta si usas gunicorn)
CMD ["sh", "-c", "flask db upgrade || true && python app.py"]