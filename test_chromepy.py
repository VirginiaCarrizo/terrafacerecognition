import socketio
import logging

# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def cliente(dni_confirmed):
    """
    Función para enviar el valor de dni_confirmed a otro servidor mediante SocketIO.
    """
    sio = socketio.Client()

    try:
        # Conectar al servidor SocketIO
        sio.connect('http://190.11.32.34:5000')  # Reemplaza con la IP y el puerto correctos

        # Registrar la conexión exitosa
        logging.info("Conectado al servidor SocketIO.")

        # Enviar el evento 'dni_confirmed_event' con el dato dni_confirmed
        logging.info(f"Enviando dni_confirmed: {dni_confirmed}")
        sio.emit('dni_confirmed_event', {'dni_confirmed': dni_confirmed})

    except Exception as e:
        # Manejar cualquier error de conexión o emisión
        logging.error(f"Error al conectar o enviar el mensaje: {e}")
    finally:
        # Cerrar la conexión SocketIO
        sio.disconnect()
        logging.info("Desconectado del servidor SocketIO.")



dni_confirmed = "12345678"  # Reemplaza con el valor real del DNI confirmado
cliente(dni_confirmed)