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
import logging
import asyncio
from playwright.async_api import async_playwright
# Importaciones adicionales para Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/terrarrhh'
socketio = SocketIO(app)
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
    logging.info("Cliente conectado")

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

@app.route('/terrarrhh/generalfood')
def general_food():
    return render_template('index_gfood.html')

@app.route('/terrarrhh/submit_cuil', methods=['POST'])
def submit_cuil():
    global cuil_value
    cuil_value = request.json.get('cuil')
    socketio.emit('cuil_received', {'cuil': cuil_value})
    return jsonify({'status': 'success'})

with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, employeesIds = encodeListKnownWithIds

@app.route('/terrarrhh/camara')
def camara():
    return render_template('camara.html')

@app.route('/terrarrhh/submit_image', methods=['POST'])
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

                    socketio.emit('confirm_dni', {'dni': dni, 'dni_modificado': dni_str[2:-1], 'nombre_apellido': employeeInfo['nombre_apellido']})
                    return jsonify({"status": "confirmation_pending"})

        logging.info("No se encontró coincidencia, se solicita ingreso manual del DNI.")
        return jsonify({"status": "no_match"})

    except Exception as e:
        logging.info(f"Error en el reconocimiento facial: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error en el servidor"}), 500
    
@socketio.on('confirm_dni_response')
def confirm_dni_response(data):
    dni_confirmed = data['confirmed']
    dni = data['dni']
    dni = str(dni)
    dni_confirmed = str(dni_confirmed)

    if dni_confirmed:
        ref = db.reference(f'Employees/{dni}')
        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        nro_orden = ref.child('order_general_food').get()
        ref.child('order_general_food').set(nro_orden + 1)

        emit('dni_confirmation_result', {'status': 'success', 'dni': dni})
    else:
        emit('dni_confirmation_result', {'status': 'denied', 'dni': dni})

# Función para ejecutar el evento de forma asincrónica en Flask-SocketIO
# @socketio.on('open_page_and_enter_dni')
# def handle_open_page_and_enter_dni(data):
#     dni = data['dni']
#     asyncio.run(open_page_and_enter_dni(dni))  # Ejecuta la función asincrónica

# # Función para abrir la página y completar el DNI utilizando Playwright
# async def open_page_and_enter_dni(dni):
#     url = "https://generalfoodargentina.movizen.com/pwa/inicio"
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)  # Ejecuta en modo headless
#         page = await browser.new_page()
#         await page.goto(url)
#         logging.info("Página abierta en el navegador.")
        
#         try:
#             # Ajusta el selector según el atributo del campo de entrada de DNI
#             dni_input = await page.wait_for_selector("dni_input", timeout=30000)  # Cambia por el selector correcto
#             await dni_input.fill(dni)
#             await dni_input.press("Enter")
#             logging.info("DNI ingresado correctamente.")
#         except Exception as e:
#             logging.error(f"Error al ingresar el DNI: {e}")
#         finally:
#             await browser.close()

# def open_page_and_enter_dni(dni):
#     """Abre la página y completa el DNI en el campo de entrada usando Selenium."""
#     url = "https://generalfoodargentina.movizen.com/pwa/inicio"

#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")
#     # chrome_options.add_argument("--no-sandbox")
#     # chrome_options.add_argument("--disable-dev-shm-usage")
#     # chrome_options.add_argument("--disable-gpu")

#     # Utiliza ChromeDriverManager para manejar el driver
#     driver = webdriver.Chrome(options=chrome_options)

#     try:
#         driver.get(url)
#         logging.info("Página abierta en el navegador.")

#         wait = WebDriverWait(driver, 10)
#         # Ajusta el selector según el atributo del campo de entrada de DNI
#         # Por ejemplo, si el campo tiene id="dni_input"
#         dni_input = wait.until(EC.presence_of_element_located((By.ID, "dni_input")))
#         dni_input.send_keys(dni)
#         dni_input.submit()
#         logging.info("DNI ingresado correctamente.")
#     except Exception as e:
#         logging.error(f"Error al ingresar el DNI: {e}")
#     finally:
#         driver.quit()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True, port=5000, debug=True)
