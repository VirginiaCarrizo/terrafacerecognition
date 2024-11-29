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
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and Chromedriver
RUN apt-get update -qq -y && \
    apt-get install -y \
    libgtk-3-0 \
    xdg-utils \
    wget && \
    wget -q -O chrome-linux64.zip https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./chrome-linux64.zip && \
    wget -q -O chromedriver.zip https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip && \
    unzip chromedriver.zip && \
    mv chromedriver /usr/local/bin/ && \
    rm chromedriver.zip

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Clean user profile before starting Chrome
CMD rm -rf /root/.config/google-chrome/Default && \
    Xvfb :99 -screen 0 1920x1080x24 & \
    python3 app.py
