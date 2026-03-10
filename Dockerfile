# Base ligera pero con soporte para paquetes
FROM python:3.11-slim-bookworm

# Instala todas las dependencias del sistema necesarias ANTES de wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    libfontconfig1 \
    libxrender1 \
    libjpeg62-turbo \
    libssl3 \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Descarga e instala wkhtmltopdf (versión 0.12.6.1 estable para bookworm)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-3.bookworm_amd64.deb || true \
    && apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb

# Verifica que wkhtmltopdf esté instalado (esto falla el build si no está)
RUN wkhtmltopdf --version

# Configura el directorio de trabajo
WORKDIR /app

# Copia requirements primero para cachear pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la app
COPY . .

# Expone el puerto (Railway lo usa automáticamente)
EXPOSE 5000

# Comando de inicio (ejecuta migraciones si usas Flask-Migrate, luego la app)
CMD ["sh", "-c", "flask db upgrade || true && python app.py"]