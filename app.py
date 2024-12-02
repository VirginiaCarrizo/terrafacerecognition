from flask import Flask
from flask_socketio import SocketIO
from routes import configure_routes
from bbdd_conection import initialize_firebase  # Configuración de Firebase
from socketio_events import configure_socketio_events # Importar configuración de eventos

app = Flask(__name__, static_url_path='/terrarrhh/static', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*", path='/terrarrhh/socket.io', transports=["websocket", "polling"])

# Configurar Firebase
db, bucket = initialize_firebase()

# Configurar rutas
configure_routes(app, socketio, db, bucket)

# Configurar eventos de SocketIO
configure_socketio_events(socketio)