# Etapa 1: Construcción para instalar las dependencias
#FROM python:3.8.19

# Establecemos el directorio de trabajo dentro del contenedor
#WORKDIR /app

# Copiamos el archivo de requerimientos
#COPY . .

# Instalamos las dependencias en un directorio temporal
# RUN apt-get update && apt-get install -y \
#    libgl1-mesa-glx \
#    texlive-xetex \
#    texlive-fonts-recommended \
#    texlive-plain-generic


# RUN pip install -r requirements.txt



# Definimos el comando de inicio de la aplicación
# CMD ["python", "app.py"]

# Etapa 1: Instalación de dependencias del sistema
FROM python:3.11.9 AS base

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos las dependencias del sistema
RUN apt-get update && apt-get install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Etapa 2: Instalación de dependencias de Python
FROM base AS builder

# Copiamos el archivo de requerimientos
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Etapa final: Construcción de la imagen final
FROM base

# Copiamos las dependencias de Python desde la etapa de construcción
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages

# Copiamos el resto de los archivos de la aplicación
COPY . .

# Definimos el comando de inicio de la aplicación
CMD ["python", "app.py"]

