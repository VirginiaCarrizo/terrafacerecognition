import logging
from flask_socketio import emit
from facerecognition import get_global_dni, update_global_dni
from base_de_datos.bbdd import actualizar_bd_dni, actualizar_bd_cuil

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def configure_socketio_events(socketio, db):
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
        actualizacion=''
        if confirmed:
            actualizacion = actualizar_bd_cuil(db, cuil)
            
            logging.info(f'actualizacion: {actualizacion}')
            # if actualizacion == 'pedido':
            #     update_global_dni(0)
            #     emit('alertas', {'status': 'denied', 'actualizacion': actualizacion}) 
            if actualizacion == 'registrado' or actualizacion == 'pedido':
                update_global_dni(str(cuil)[2:-1])
                dni = get_global_dni()
                logging.info(f'dni: {dni}')
                emit('alertas', {'status': 'success', 'actualizacion': 'registrado'})
            elif actualizacion == 'nomach':
                update_global_dni(0)
                emit('alertas', {'status': 'denied', 'actualizacion': actualizacion})
        else:
            update_global_dni(0)
            emit('alertas', {'status': 'denied', 'actualizacion': actualizacion})

    @socketio.on('update_db')
    def update_db(dni):
        actualizacion = actualizar_bd_dni(db, dni)
        if actualizacion == 'registrado' or actualizacion == 'pedido':
            # if actualizacion == 'pedido':
            #     update_global_dni(0)
            #     emit('alertas', {'status': 'denied', 'actualizacion': actualizacion})
            if actualizacion == 'registrado' or actualizacion == 'pedido':
                update_global_dni(dni)
                emit('alertas', {'status': 'success', 'actualizacion': actualizacion})
        elif actualizacion == 'nomach':
            update_global_dni(0)
            logging.info('NO SE ENCONTRO COINCIDENCIA EN LA BASE DE DATOS')
            emit('alertas', {'status': 'denied', 'actualizacion': actualizacion})  
            return



