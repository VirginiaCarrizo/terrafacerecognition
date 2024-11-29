# Use an official Python runtime as a parent image
FROM python:3.11-bullseye

# Install system dependencies
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
        gnupg2 \
        unzip \
        xvfb \
        python3-pip \
        wget \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome.deb && \
    rm google-chrome.deb

# Install Chromedriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Clean user profile before starting Chrome and run the Flask app with Xvfb
CMD rm -rf /root/.config/google-chrome/Default && \
    Xvfb :99 -screen 0 1920x1080x24 & \
    python3 app.py
