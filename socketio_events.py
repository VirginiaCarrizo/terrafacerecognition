import logging
from flask_socketio import emit
from datetime import datetime

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def configure_socketio_events(socketio, db):
    """Configura los eventos de SocketIO."""
    @socketio.on('connect')
    def handle_connect():
        logging.info("Cliente conectado")

    # @socketio.on('confirm_dni_response')
    # def confirm_dni_response(data):
    #     dni_confirmed = data['confirmed']
    #     dni = data['dni']
    #     dni = str(dni)
    #     dni_confirmed = str(dni_confirmed)

    #     if dni_confirmed:
    #         ref = db.reference(f'Employees/{dni}')
    #         ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    #         nro_orden = ref.child('order_general_food').get()
    #         ref.child('order_general_food').set(nro_orden + 1)
    #         logging.info("antes de entrar al with.")

    #         emit('dni_confirmation_result', {'status': 'success', 'dni': dni})
    #     else:
    #         emit('dni_confirmation_result', {'status': 'denied', 'dni': dni})

