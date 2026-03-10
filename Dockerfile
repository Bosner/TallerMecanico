FROM python:3.11-slim-bookworm

# Instala dependencias del sistema (exhaustivo para wkhtmltopdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libfontconfig1 \
    libxrender1 \
    libjpeg62-turbo \
    libssl3 \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Descarga e instala wkhtmltopdf 0.12.6.1 para bookworm (AMD64)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -O /tmp/wkhtmltox.deb \
    && dpkg -i /tmp/wkhtmltox.deb || apt-get install -f -y \
    && rm /tmp/wkhtmltox.deb

# Fuerza link al PATH y actualiza ldconfig por si acaso
RUN ln -sf /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf \
    && ldconfig

# Verifica instalación (debe mostrar versión si todo OK)
RUN wkhtmltopdf --version || echo "Verificación falló, pero continuamos" && which wkhtmltopdf

# Directorio de la app
WORKDIR /app

# Copia y instala requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto
COPY . .

EXPOSE 5000

# Comando de inicio (migraciones + app)
CMD ["sh", "-c", "flask db upgrade || true && python app.py"]