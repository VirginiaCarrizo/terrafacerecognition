import logging
from flask_socketio import emit
from datetime import datetime
from globals import global_dni
from routes import dni_lock
from facerecognition import submit_dni, get_global_dni, update_global_dni
from bbdd import actualizar_bd

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
        update_global_dni(str(cuil)[2:-1])
        dni = get_global_dni()
        logging.info(f'dni desde confirm dni response {dni}')
        actualizacion=''
        if confirmed:
            actualizacion = actualizar_bd(db, cuil)
            if actualizacion == 'pedido':
                emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})
            elif actualizacion == 'registrado':
                emit('actualizacion_bd', {'status': 'success', 'actualizacion': actualizacion})
            elif actualizacion == 'nomach':
                emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})
        else:
            emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})

    @socketio.on('update_db')
    def update_db(dni):
        update_global_dni(dni)
        new_dni = get_global_dni()
        logging.info(f'new_dni desde update_db: {new_dni}')

        employees_ref = db.reference(f'Employees/')
        employees = employees_ref.get()
        actualizacion=''
        if not employees:
            return None

        for cuil, datos in employees.items():
            # Asegurarse de que el CUIL tenga al menos 11 caracteres
            if len(cuil) >= 11:
                # Extraer los dígitos desde el tercer hasta el anteúltimo
                segmento_cuil = cuil[2:-1]
                
                # Comparar con el DNI proporcionado
                if segmento_cuil == str(dni):

                    logging.info(f'cuil: {cuil}, datos: {datos}')
                    actualizacion=actualizar_bd(db, cuil)
                    if actualizacion == 'pedido':
                        emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})
                    elif actualizacion == 'registrado':
                        emit('actualizacion_bd', {'status': 'success', 'actualizacion': actualizacion})
                    elif actualizacion == 'nomach':
                        emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})  
                    return
                # Si no se encuentra ninguna coincidencia
        logging.info('NO SE ENCONTRO COINCIDENCIA EN LA BASE DE DATOS')
        update_global_dni(0)
        emit('actualizacion_bd', {'status': 'denied', 'actualizacion': actualizacion})
        return



