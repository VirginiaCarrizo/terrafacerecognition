from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import firebase_admin
from firebase_admin import credentials, db, storage
import cv2
import numpy as np 
import base64
import face_recognition
import pickle
from datetime import datetime
import re

app = Flask(__name__)
socketio = SocketIO(app)  # Inicializar Flask-SocketIO
cuil_value = ""  # Variable global para almacenar el cuil

# Inicializar Firebase Admin
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
    'storageBucket': "terra-employees.appspot.com"
})
bucket = storage.bucket()

@app.route('/terrarrhh')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print("Cliente conectado")

# Ruta para agregar un registro a Firebase
@app.route('/terrarrhh/agregar_registro', methods=['POST'])
def agregar_registro():
    try:
        data = request.form  # Mantén request.form, ya que estamos usando FormData
        # Crea un diccionario para almacenar los datos del registro
        nombre_completo = f"{data['nombre']} {data['apellido']}"
        data_dict = {
            'legajo': data['legajo'],
            'nombre_apellido': nombre_completo,
            'cuil': data['cuil'],
            'empresa': data['empresa'],
            'fecha_nacimiento': data['fecha-nacimiento'],
            'rol': data['rol'],
            'sector': data['sector']
        }

        # Verificar si hay una foto adjunta
        if 'foto' in request.files:

            foto = request.files['foto']

            blob = storage.bucket().blob(f"Images/{data_dict['nombre_apellido']}.png")  # Usamos el legajo como identificador
            blob.upload_from_file(foto, content_type='image/png')  # Especificamos el tipo MIME correcto
            blob.make_public()
            foto_url = blob.public_url  # Generar URL pública de la foto
            data_dict['foto'] = foto_url  # Agregar la URL de la foto al nuevo diccionario

        

        # Usar el legajo como key en la base de datos
        ref = db.reference('Employees')
        ref.child(data['cuil']).set(data_dict)  # Guardar el nuevo diccionario en Firebase

        return jsonify({'status': 'success', 'message': 'Registro agregado correctamente', 'registro': data_dict, 'cuil': data['cuil']})

    except Exception as e:
        print(f"Error al agregar registro: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500

@app.route('/terrarrhh/buscar_registro', methods=['POST'])
def buscar_registro():
    try:
        search_term = request.json.get('search_term', '').lower().strip()  # Obtenemos el término de búsqueda en minúsculas

        ref = db.reference('Employees')
        registros = ref.get()  # Obtenemos todos los registros de Firebase

        if registros is None:
            return jsonify([])  # Si no hay registros, devolvemos una lista vacía
        

        resultados = []

        for key, value in registros.items():
            nombre_completo = value.get('nombre_apellido', '').lower()  # Unificamos nombre y apellido
            cuil = str(value.get('cuil', ''))

            # Buscamos coincidencias en 'nombre_completo' o 'cuil'
            if search_term in nombre_completo or search_term in cuil:
                # Obtener la imagen del storage usando el ID
                # print(f'Images/{nombre_completo.upper()}.png')
                blob = bucket.blob(f'Images/{nombre_completo.upper()}.png')
                if blob.exists():
                    # Descargar la imagen como un array y decodificarla
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    img = cv2.imdecode(array, cv2.IMREAD_COLOR)  # Decodificar a imagen de OpenCV

                    # Codificar la imagen a base64
                    _, img_encoded = cv2.imencode('.png', img)
                    img_base64 = base64.b64encode(img_encoded).decode('utf-8')

                    # Añadir la imagen a los resultados en base64
                    value['foto'] = img_base64

                else:
                    value['foto'] = None  # No existe la imagen

                resultados.append(value)

        return jsonify(resultados)  # Devolvemos los registros que coinciden con la búsqueda
    except Exception as e:
        print(f"Error en la búsqueda: {str(e)}")
        return jsonify({'error': 'Ocurrió un error en el servidor'}), 500
    
# Ruta para modificar un registro existente en Firebase
@app.route('/terrarrhh/modificar_registro/<cuil>', methods=['POST'])
def modificar_registro(cuil):
    data = request.json
    ref = db.reference(f'Employees/{cuil}')  # Usamos el legajo como identificador

    ref.update({
        'legajo': data['legajo'],
        'nombre_apellido': data['nombre_apellido'],
        'cuil': cuil,
        'empresa': data['empresa'],
        'fecha_nacimiento': data['fecha_nacimiento'],
        'rol': data['rol'],
        'sector': data['sector']
    })

    return jsonify({'status': 'success', 'message': 'Registro modificado correctamente'})

@app.route('/terrarrhh/eliminar_registro', methods=['POST'])
def eliminar_registro():
    try:
        data = request.get_json()  # Obtener el JSON enviado desde el cliente
        ref = db.reference(f'Employees/{data["cuil"]}')  # Usar la key para eliminar el registro
        registro = ref.get()  # Obtener el registro actual antes de eliminarlo
        nombre_apellido = registro["nombre_apellido"]

        if registro and 'foto' in registro:
            # Referencia al archivo en Firebase Storage
            blob = bucket.blob(f"Images/{nombre_apellido}.png")
            blob.delete()  # Eliminar la imagen de Firebase Storage


        ref.delete()  # Eliminar el registro de la base de datos
        return jsonify({'status': 'success', 'message': 'Registro eliminado correctamente'})
    except Exception as e:
        print(f"Error al eliminar registro y foto: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500


@app.route('/generalfood')
def general_food():
    return render_template('index_gfood.html')

@app.route('/submit_cuil', methods=['POST'])
def submit_cuil():
    global cuil_value
    cuil_value = request.json.get('cuil')  # Captura el cuil enviado desde el reconocimiento facial
    socketio.emit('cuil_received', {'cuil': cuil_value})  # Emitir el evento para que sea utilizado en /generalfood
    return jsonify({'status': 'success'})


# Cargar el archivo de codificación
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, employeesIds = encodeListKnownWithIds

@app.route('/camara')
def camara():
    return render_template('camara.html')

@app.route('/submit_image', methods=['POST'])
def submit_image():
    try:
        # Recibir la imagen desde el cliente (base64)
        data = request.json['image']
        image_data = data.split(',')[1]  # Eliminar el prefijo "data:image/png;base64,"
        npimg = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # Procesar la imagen (reconocimiento facial)
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                # Comparar con los "encodings" conocidos de Firebase
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
                            break
                    
                    cuil=employeeInfo['cuil']
                    # Actualizar la hora de asistencia
                    ref = db.reference(f'Employees/{cuil}')

                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    nro_orden = ref.child('order_general_food').get()
                    ref.child('order_general_food').set(nro_orden+1)

                    # Emitir el cuil a través de Socket.IO
                    socketio.emit('cuil_received', {'cuil': cuil})

                    # Devolver el nombre y cuil del empleado
                    return jsonify({"nombre_apellido": employeeInfo['nombre_apellido'], "cuil": cuil})

        return jsonify({"error": "No se encontró una coincidencia"})

    except Exception as e:
        print(f"Error en el reconocimiento facial: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500








# if __name__ == '__main__':
#     socketio.run(app, debug=True)





# if __name__ == '__main__':
#     app.run(debug=True)
