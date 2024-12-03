from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from login import configure_login
from routes import configure_routes
from bbdd_conection import initialize_firebase  # Configuración de Firebase
from socketio_events import configure_socketio_events # Importar configuración de eventos
from user import users

app = Flask(__name__, static_url_path='/terrarrhh/static', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*", path='/terrarrhh/socket.io', transports=["websocket", "polling"])
app.secret_key = 'terragene'  # Necesario para las sesiones

# Configurar Firebase
db, bucket = initialize_firebase()

# Configurar rutas
configure_routes(app, socketio, db, bucket)

# Configurar eventos de SocketIO
configure_socketio_events(socketio, db)

# Configurar LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "https://terragene.life/terrarrhh"  # Vista para redirigir si el usuario no está autenticado

@login_manager.user_loader
def load_user(user_id):
    # Aquí estás buscando al usuario desde el diccionario `users` que tienes en `user.py`
    return users.get(user_id)

configure_login(app)