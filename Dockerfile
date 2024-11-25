# Usa una imagen base de Python con Debian Buster
FROM python:3.11-bullseye

# Instala dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    apt-utils \ 
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
    chromium \
    chromium-driver \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Instala Google Chrome y Chromium Driver
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Instalar la versión específica de ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/131.0.6778.85/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto de Flask y VNC
EXPOSE 5000

# Limpia el perfil de usuario antes de iniciar Chrome
CMD rm -rf /root/.config/google-chrome/Default && \
    Xvfb :99 -screen 0 1920x1080x24 & \
    python3 app.py