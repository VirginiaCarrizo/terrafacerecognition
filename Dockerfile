# Usa una imagen base de Python
FROM python:3.11

# Instala CMake, build-essential, y libgl1
RUN apt-get update && \
    apt-get install -y cmake build-essential libgl1 xvfb && \
    apt-get clean

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias y lo instala
COPY requirements.txt requirements.txt
RUN pip install -v --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al contenedor
COPY . .

# Expone el puerto de Flask (5000 por defecto)
EXPOSE 5000

CMD Xvfb :0 -screen 0 1024x768x16 & python app.py
