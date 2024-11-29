from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
import firebase_admin
import logging
import socketio

# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__, static_url_path='/terrarrhh/static', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*", path='/terrarrhh/socket.io', transports=["websocket", "polling"])
cuil_value = ""  # Variable global para almacenar el cuil

@app.route('/terrarrhh', strict_slashes=False)
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logging.info("Cliente conectado")


@app.route('/terrarrhh/generalfood')
def general_food():
    return render_template('index_gfood.html')

@app.route('/terrarrhh/submit_cuil', methods=['POST'])
def submit_cuil():
    global cuil_value
    cuil_value = request.json.get('cuil')
    socketio.emit('cuil_received', {'cuil': cuil_value})
    return jsonify({'status': 'success'})

@app.route('/terrarrhh/camara')
def camara():
    return render_template('camara.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True, port=5000, debug=True)
