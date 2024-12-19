import logging
from flask_socketio import emit
from facerecognition import get_global_dni, update_global_dni
from base_de_datos.bbdd import actualizar_bd_dni, buscar_empleados

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def configure_socketio_events(socketio, db, bucket):
    """Configura los eventos de SocketIO."""
    @socketio.on('connect')
    def handle_connect():
        logging.info("Cliente conectado")

    @socketio.on('update_dni_global')
    def update_dni_global(dni):
        update_global_dni(dni)

    @socketio.on('confirm_dni_response')
    def confirm_dni_response(data):
        confirmed = data['confirmed']
        cuil = data['cuil']
        dni = data['dni']
        if confirmed:
            if cuil != None and dni == None:
                macht = buscar_empleados(cuil, db, bucket)
                if macht:
                    logging.info(f"macht: {macht}")
                    update_global_dni(str(cuil)[2:-1])
                    logging.info(get_global_dni())
                    emit('alertas', {'status': 'success', 'actualizacion': 'registrado'})
                else:
                    update_global_dni(0)
                    emit('alertas', {'status': 'denied', 'actualizacion': 'nomacht'})
            else:
                macht = buscar_empleados(dni, db, bucket)
                if macht:
                    update_global_dni(dni)
                    emit('alertas', {'status': 'success', 'actualizacion': 'registrado'})
                else:
                    update_global_dni(0)
                    emit('alertas', {'status': 'denied', 'actualizacion': 'nomacht'})
        else:
            update_global_dni(0)
            emit('alertas', {'status': 'denied', 'actualizacion': 'noconfirm'})

