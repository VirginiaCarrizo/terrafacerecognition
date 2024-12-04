from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from functools import wraps
from user import users
from bbdd import agregar_empleado, buscar_empleados, modificar_empleado, eliminar_empleado
from facerecognition import facerec, submit_dni
import logging

# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

routes = Blueprint('routes', __name__)  # Crear un Blueprint para las rutas

# DECORADOR PARA VERIFICAR LOS ROLES
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)  # Error de acceso denegado si no está autenticado
            if current_user.role not in roles:
                abort(403)  # Error de acceso denegado si no tiene el rol adecuado
            return fn(*args, **kwargs)
        return wrapped
    return wrapper

def configure_routes(app, socketio, db, bucket):
    """Configura las rutas y eventos asociados."""

    # RENDERIZACIONES DE VISTAS
    @routes.route('/terrarrhh', strict_slashes=False)
    @login_required
    @role_required('admin', 'terrarrhh')
    def index():
        return render_template('index.html')

    @routes.route('/terrarrhh/generalfood')
    @login_required
    def general_food():
        return render_template('index_gfood.html')

    @routes.route('/terrarrhh/camara')
    @login_required
    @role_required('admin', 'generalfood')
    def camara():
        return render_template('camara.html')
    
    @routes.route('/terrarrhh/submit_cuil', methods=['POST'])
    def submit_cuil():
        global cuil_value
        cuil_value = request.json.get('cuil')
        socketio.emit('cuil_received', {'cuil': cuil_value})
        return jsonify({'status': 'success'})


    # ENDPOINT PARA EL RECONOCIMIENTO FACIAL
    @routes.route('/terrarrhh/submit_image', methods=['POST'])
    def submit_image():
            dni, dnis, cuil_str, employeeInfoCompletaBD = facerec(db)
            if dni and dnis and cuil_str and employeeInfoCompletaBD:
                socketio.emit('confirm_dni', {'dni': dni, 'employeeInfoCompletaBD': employeeInfoCompletaBD})
                return jsonify({"status": "confirmation_pending"})
            else:
                logging.info("No se encontró coincidencia, se solicita ingreso manual del DNI.")
                return jsonify({"status": "no_match"})


    # ENDPOINT PARA EL SCRIPT LOCAL
    @routes.route('/get_dni', methods=['GET'])
    def get_dni():
        dni = submit_dni()
        logging.info(f'DDDDDDDDDDDDDDDDDDDDNIIIIIIIIIIIIIIIIIIIIIIIIIIIIII: {dni}')
        if dni:
            return jsonify({"status": "success", "dni": dni}), 200
        else:
            return jsonify({"status": "error", "message": "Error processing request"}), 500
        
        

    # ENDOPOINTS PARA INTERACTUAR CON LA BASE DE DATOS FIREBASE
    @routes.route('/terrarrhh/agregar_registro', methods=['POST'])
    @login_required
    @role_required('admin', 'terrarrhh')
    def agregar_registro():
        try:
            data = request.form
            foto = request.files['foto']
            empleado = agregar_empleado(data, foto, db, bucket)

            return jsonify({'status': 'success', 'message': 'Registro agregado correctamente', 'registro': empleado, 'cuil': data['cuil']})

        except Exception as e:
            logging.info(f"Error al agregar registro: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500

    @routes.route('/terrarrhh/buscar_registro', methods=['POST'])
    @login_required
    @role_required('admin', 'terrarrhh')
    def buscar_registro():
        try:
            if not request.json or 'search_term' not in request.json:
                return jsonify({'error': 'Falta el campo "search_term" en la solicitud'}), 400
            
            search_term = request.json.get('search_term', '').lower().strip()
            resultados = buscar_empleados(search_term, db, bucket)

            return jsonify(resultados)
        
        except Exception as e:
            logging.info(f"Error en la búsqueda: {str(e)}")
            return jsonify({'error': 'Ocurrió un error en el servidor'}), 500

    @routes.route('/terrarrhh/modificar_registro/<cuil>', methods=['POST'])
    @login_required
    @role_required('admin', 'terrarrhh')
    def modificar_registro(cuil):
        try:
            data = request.json
            modificar_empleado(cuil, data, db, bucket)

            return jsonify({'status': 'success', 'message': 'Registro modificado correctamente'})
        except Exception as e:
            logging.error(f"Error en /modificar_registro: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @routes.route('/terrarrhh/eliminar_registro', methods=['POST'])
    @login_required
    @role_required('admin', 'terrarrhh')
    def eliminar_registro():
        try:
            data = request.get_json()
            cuil = data.get("cuil")

            if not cuil:
                return jsonify({'status': 'error', 'message': 'Falta el campo "cuil" en la solicitud'}), 400


            if eliminar_empleado(cuil, db, bucket):
                return jsonify({'status': 'success', 'message': 'Registro eliminado correctamente'})
            else:
                return jsonify({'status': 'error', 'message': 'Registro no encontrado'}), 404
            
        except Exception as e:
            logging.info(f"Error al eliminar registro y foto: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500
    
    
    # Registrar el Blueprint al final
    app.register_blueprint(routes)