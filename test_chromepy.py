import socketio

# Dirección del servidor Flask-SocketIO en AWS
SERVER_URL = "http://54.81.210.167:5000"  # Cambia <IP_PUBLICA_AWS> por la dirección pública de tu instancia

# Crear cliente SocketIO
sio = socketio.Client()

# Definir eventos
@sio.on('connect')
def on_connect():
    print("Conectado al servidor Flask-SocketIO en AWS!")

@sio.on('response_to_local')
def on_response(data):
    print(f"Respuesta del servidor: {data}")

@sio.on('disconnect')
def on_disconnect():
    print("Desconectado del servidor.")

# Conectar al servidor
try:
    sio.connect(SERVER_URL)
    print("Conexión establecida.")
    
    # Enviar un mensaje al servidor
    mensaje = {"message": "Hola desde el script local!"}
    sio.emit('message_from_local', mensaje)
    print("Mensaje enviado.")
    
    # Mantener la conexión
    sio.wait()
except Exception as e:
    print(f"Error al conectar: {e}")
