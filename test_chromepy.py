from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Ruta básica opcional
@app.route('/')
def index():
    return "Servidor Flask-SocketIO en ejecución"

# Manejador del evento para recibir dni_confirmed
@socketio.on('dni_confirmed_event')
def handle_dni_confirmed_event(data):
    dni_confirmed = data.get('dni_confirmed')
    print(f"DNI confirmado recibido: {dni_confirmed}")
    # Aquí puedes procesar el dni_confirmed según lo necesites

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)