#!/bin/bash

# Elimina el archivo de bloqueo si existe
if [ -e /tmp/.X99-lock ]; then
    echo "Eliminando archivo de bloqueo /tmp/.X99-lock"
    rm -f /tmp/.X99-lock
fi

# Inicia Xvfb en display :99
Xvfb :99 -screen 0 1024x768x16 &
export DISPLAY=:99

# Espera un momento para asegurar que Xvfb inicia correctamente
sleep 2

# Verifica que Xvfb está corriendo
if xdpyinfo -display $DISPLAY > /dev/null 2>&1; then
    echo "Xvfb está corriendo en $DISPLAY"
else
    echo "Error: Xvfb no se pudo iniciar en $DISPLAY"
    exit 1
fi

# Ejecuta tu aplicación
python app.py
