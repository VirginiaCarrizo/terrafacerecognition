# Usa una imagen base de Python con Debian Buster
FROM python:3.11-buster

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
    libx11-xcb1 \
    libdrm2 \
    libxcursor1 \
    libxss1 \
    libappindicator3-1 \
    libxcomposite1 \
    libasound2 \
    libgbm1 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libcurl3-gnutls \
    fonts-liberation \
    libgtk-3-0 \
    libxdamage1 \
    libxfixes3 \
    libxext6 \
    libgl1-mesa-glx \
    wget \
    gnupg2 \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*
    

# Instala Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Instala ChromeDriver
RUN CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q -O /tmp/chromedriver_linux64.zip "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

# Instala Playwright y sus navegadores
RUN pip install --no-cache-dir playwright && \
    playwright install

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
