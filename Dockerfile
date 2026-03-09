# Usa una imagen base de Python oficial (elige la versión que usas localmente, ej: 3.11 o 3.12)
FROM python:3.11-slim

# Instala dependencias del sistema necesarias para wkhtmltopdf y pdfkit
RUN apt-get update && apt-get install -y \
    wget \
    libfontconfig1 \
    libxrender1 \
    libjpeg62-turbo \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Descarga e instala wkhtmltopdf (versión estable 0.12.6)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-3.bookworm_amd64.deb || apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb

# Verifica instalación
RUN wkhtmltopdf --version

# Copia tu app
WORKDIR /app
COPY . .

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Puerto de Flask (Railway lo expone automáticamente)
EXPOSE 5000

# Comando para correr la app (ajusta si usas gunicorn o similar)
CMD ["python", "app.py"]