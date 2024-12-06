import logging
from flask_socketio import emit
from datetime import datetime
from globals import global_dni
from routes import dni_lock
from facerecognition import submit_dni, get_global_dni, update_global_dni

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def configure_socketio_events(socketio, db):
    """Configura los eventos de SocketIO."""
    @socketio.on('connect')
    def handle_connect():
        logging.info("Cliente conectado")

    @socketio.on('confirm_dni_response')
    def confirm_dni_response(data):
        confirmed = data['confirmed']
        cuil = data['cuil']
        if confirmed:
            ref = db.reference(f'Employees/{cuil}')
            ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            nro_orden = ref.child('order_general_food').get()
            ref.child('order_general_food').set(nro_orden + 1)

            emit('wait_print', {'status': 'success', 'cuil': cuil})
        else:
            emit('wait_print', {'status': 'denied', 'cuil': cuil})

    @socketio.on('update_db')
    def update_db(dni):
        update_global_dni(dni)
        new_dni = get_global_dni()
        logging.info(f'new_dni desde update_db: {new_dni}')
        # logging.info(global_dni)
        logging.info(db.reference(f'Employees/'))
        # ref = db.reference(f'Employees/{cuil}')
        # ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # nro_orden = ref.child('order_general_food').get()
        # ref.child('order_general_food').set(nro_orden + 1)


