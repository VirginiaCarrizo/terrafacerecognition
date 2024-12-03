from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from login import auth
from user import users
from bbdd import agregar_empleado, buscar_empleados, modificar_empleado, eliminar_empleado
import base64
import face_recognition
import cv2
import numpy as np 
import logging
from threading import Lock
import pickle
from datetime import datetime

# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, employeesIds = encodeListKnownWithIds

# In-memory store for DNIs with thread safety
dnis = ["44291507"]
dni_lock = Lock()
cuil_value = ""  # Variable global para almacenar el cuil

routes = Blueprint('routes', __name__)  # Crear un Blueprint para las rutas

socketio_routes = []  # Opcional: lista para manejar eventos SocketIO globalmente
# Decorador para verificar roles
def role_required(*roles):
    try:
        def wrapper(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if current_user.role not in roles:
                    abort(403)  # Error de acceso denegado
                return fn(*args, **kwargs)
            return wrapped
        return wrapper
    except Exception as e:
        logging.error(f'Error en role required {e}')

def configure_routes(app, socketio, db, bucket):
    """Configura las rutas y eventos asociados."""

    @routes.route('/terrarrhh', strict_slashes=False)
    @login_required
    @role_required('admin', 'terrarrhh')
    def index():
        return render_template('index.html')

    @routes.route('/terrarrhh/generalfood')
    @login_required
    def general_food():
        return render_template('index_gfood.html')

    @routes.route('/terrarrhh/submit_cuil', methods=['POST'])
    def submit_cuil():
        global cuil_value
        cuil_value = request.json.get('cuil')
        socketio.emit('cuil_received', {'cuil': cuil_value})
        return jsonify({'status': 'success'})

    @routes.route('/terrarrhh/camara')
    @login_required
    @role_required('admin', 'generalfood')
    def camara():
        return render_template('camara.html')

    @routes.route('/terrarrhh/submit_image', methods=['POST'])
    def submit_image():
        try:
            data = request.json['image']
            image_data = data.split(',')[1]
            npimg = np.frombuffer(base64.b64decode(image_data), np.uint8)
            img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

            faceCurFrame = face_recognition.face_locations(imgS)
            encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
            logging.info(faceCurFrame)
            if faceCurFrame:
                for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                    matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                    faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                    matchIndex = np.argmin(faceDis)
                    if matches[matchIndex]:
                        id = employeesIds[matchIndex]
                        employeesRef = db.reference(f'Employees').get()
                        employeeInfo = None
                        for key, value in employeesRef.items():
                            if value['nombre_apellido'] == id:
                                employeeInfo = value
                                logging.info(f'employeeInfo: {employeeInfo}')
                                break

                        dni = employeeInfo['cuil']
                        dni_str = str(dni)
                        ref = db.reference(f'Employees/{dni}')

                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        nro_orden = ref.child('order_general_food').get()
                        ref.child('order_general_food').set(nro_orden + 1)
                        dnis.append(dni_str[2:-1])

                        socketio.emit('confirm_dni', {'dni': dni, 'dni_modificado': dni_str[2:-1], 'nombre_apellido': employeeInfo['nombre_apellido']})
                        return jsonify({"status": "confirmation_pending"})

            logging.info("No se encontró coincidencia, se solicita ingreso manual del DNI.")
            return jsonify({"status": "no_match"})

        except Exception as e:
            logging.info(f"Error en el reconocimiento facial: {e}")
            return jsonify({"status": "error", "message": "Ocurrió un error en el servidor"}), 500

    # Endpoint for PC to retrieve DNI data
    @routes.route('/get_dni', methods=['GET'])
    def get_dni():
        try:
            with dni_lock:
                if not dnis:
                    return jsonify({"status": "no_dni", "message": "No DNI available"}), 200
                # Retrieve the first DNI in the list
                dni = dnis.pop(0)
            logging.info(f"Sending DNI to PC: {dni}")
            return jsonify({"status": "success", "dni": dni}), 200
        except Exception as e:
            logging.error(f"Error in /get_dni: {e}")
            return jsonify({"status": "error", "message": f"Error processing request: {e}"}), 500
        

    # Ruta para agregar un registro a Firebase
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
    
    @auth.route("/logout")
    @login_required
    def logout():
        logout_user()  # Cierra la sesión del usuario
        return redirect(url_for("login"))  # Redirige al login
    
    @auth.errorhandler(403)
    def forbidden(error):
        return "Access Forbidden", 403  # Mensaje que se mostrará cuando el usuario no tenga permisos
    

    # Registrar el Blueprint al final
    app.register_blueprint(routes)
    app.register_blueprint(auth)  # Rutas de autenticación