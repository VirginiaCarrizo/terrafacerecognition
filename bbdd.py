from flask import Flask, render_template, request, jsonify, abort
import firebase_admin
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
import os
from app import app, socketio
import logging
import cv2
import numpy as np 
import base64

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Construir las credenciales directamente desde las variables de entorno
cred_data = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),  # Reemplazar saltos de línea
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
}

# Inicializar Firebase Admin
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
    'storageBucket': "terra-employees.appspot.com"
})
bucket = storage.bucket()

# Ruta para agregar un registro a Firebase
@app.route('/terrarrhh/agregar_registro', methods=['POST'])
def agregar_registro():
    try:
        data = request.form
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

        if 'foto' in request.files:
            foto = request.files['foto']
            blob = storage.bucket().blob(f"Images/{data_dict['nombre_apellido']}.png")
            blob.upload_from_file(foto, content_type='image/png')
            blob.make_public()
            foto_url = blob.public_url
            data_dict['foto'] = foto_url

        ref = db.reference('Employees')
        ref.child(data['cuil']).set(data_dict)

        return jsonify({'status': 'success', 'message': 'Registro agregado correctamente', 'registro': data_dict, 'cuil': data['cuil']})

    except Exception as e:
        logging.info(f"Error al agregar registro: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500

@app.route('/terrarrhh/buscar_registro', methods=['POST'])
def buscar_registro():
    try:
        search_term = request.json.get('search_term', '').lower().strip()
        ref = db.reference('Employees')
        registros = ref.get()

        if registros is None:
            return jsonify([])

        resultados = []

        for key, value in registros.items():
            nombre_completo = value.get('nombre_apellido', '').lower()
            cuil = str(value.get('cuil', ''))

            if search_term in nombre_completo or search_term in cuil:
                blob = bucket.blob(f'Images/{nombre_completo.upper()}.png')
                if blob.exists():
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    img = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    _, img_encoded = cv2.imencode('.png', img)
                    img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                    value['foto'] = img_base64
                else:
                    value['foto'] = None

                resultados.append(value)

        return jsonify(resultados)
    except Exception as e:
        logging.info(f"Error en la búsqueda: {str(e)}")
        return jsonify({'error': 'Ocurrió un error en el servidor'}), 500

@app.route('/terrarrhh/modificar_registro/<cuil>', methods=['POST'])
def modificar_registro(cuil):
    data = request.json
    ref = db.reference(f'Employees/{cuil}')

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
        data = request.get_json()
        ref = db.reference(f'Employees/{data["cuil"]}')
        registro = ref.get()
        nombre_apellido = registro["nombre_apellido"]

        if registro and 'foto' in registro:
            blob = bucket.blob(f"Images/{nombre_apellido}.png")
            blob.delete()

        ref.delete()
        return jsonify({'status': 'success', 'message': 'Registro eliminado correctamente'})
    except Exception as e:
        logging.info(f"Error al eliminar registro y foto: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error en el servidor'}), 500
