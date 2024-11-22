# Usa una imagen base de Python con Debian Buster
FROM python:3.11-bullseye

# Instala dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    cmake \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxcursor1 \
    libxss1 \
    libxcomposite1 \
    libasound2 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgtk-3-0 \
    libxdamage1 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    fonts-liberation \
    libglu1-mesa \
    libdrm2 \
    libgbm1 \
    libxfixes3 \
    wget \
    gnupg2 \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Instala Playwright y sus navegadores
RUN pip install --no-cache-dir playwright==1.38.0

# Instala Playwright y sus navegadores
RUN pip install --no-cache-dir playwright==1.38.0 && playwright install --with-deps

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver (matching Chrome version)
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/131.0.6778.85/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver-linux64 chromedriver-linux64.zip

# Ensure Chrome is in PATH
ENV PATH="/usr/bin/google-chrome:${PATH}"

# Establece variables de entorno para Xvfb
ENV DISPLAY=:0

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Ejecuta la aplicación en Xvfb para manejar la pantalla virtual
CMD rm -f /tmp/.X0-lock && Xvfb :0 -screen 0 1024x768x16 & python app.py
