FROM python:3.11-slim-bookworm

# Instala dependencias mínimas y necesarias para wkhtmltopdf
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

# Descarga e instala wkhtmltopdf (versión bookworm AMD64)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -O /tmp/wkhtmltox.deb \
    && dpkg -i /tmp/wkhtmltox.deb || apt-get install -f -y \
    && rm /tmp/wkhtmltox.deb

# Asegura que el binario esté en PATH y actualiza librerías
ENV PATH="/usr/local/bin:${PATH}"
RUN ldconfig

# Verificación explícita con ruta completa + echo para depurar
RUN /usr/local/bin/wkhtmltopdf --version || echo "Verificación falló (ruta completa usada)" \
    && which wkhtmltopdf || echo "which no encontró wkhtmltopdf"

# Directorio y app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

# Inicio: migraciones + app
CMD ["sh", "-c", "flask db upgrade || true && python app.py"]