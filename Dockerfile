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

# Añade el repositorio de Google Chrome y su clave
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instala Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable && rm -rf /var/lib/apt/lists/*

# Instala chromedriver correspondiente a la versión de Chrome instalada
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%.*}") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Establece la variable de entorno para el PATH
ENV PATH="/usr/local/bin:/usr/bin/google-chrome:${PATH}"

# Establece variables de entorno para Xvfb
ENV DISPLAY=:99

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Ejecuta la aplicación
CMD Xvfb :99 -screen 0 1024x768x16 & python app.py