from flask import Flask, render_template, request, jsonify, abort
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
from selenium import webdriver
from selenium.webdriver import Edge, EdgeOptions, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv
from chromedriver_py import binary_path 
import socketio
import requests
from threading import Lock

# In-memory store for DNIs with thread safety
dnis = []
dni_lock = Lock()

def cliente(dni):
    try:
        url = "http://190.216.87.234:5000/receive_dni"  # Replace with your PC's public IP
        payload = {"dni": dni}
        headers = {"Content-Type": "application/json"}

        logging.info(f"Preparing to send DNI: {dni} to {url}")
        logging.debug(f"Payload: {payload}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.info(f"HTTP POST sent to {url}. Status Code: {response.status_code}")

        if response.status_code == 200:
            logging.info("DNI confirmed successfully sent. Response received.")
            logging.debug(f"Response Data: {response.json()}")
        else:
            logging.error(f"Failed to send DNI. Status Code: {response.status_code}")
            logging.error(f"Response Text: {response.text}")

    except requests.exceptions.RequestException as req_err:
        logging.error(f"HTTP request failed: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error in `cliente` function: {e}")


# Basic logger configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs to console
        logging.FileHandler("app_logs.log")  # Logs to a file for later analysis
    ]
)

app = Flask(__name__, static_url_path='/terrarrhh/static', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="https://terragene.life", path='/terrarrhh/socket.io', transports=["websocket", "polling"])
cuil_value = ""  # Global variable to store cuil

# Load environment variables from .env file
load_dotenv()

# Construct Firebase credentials from environment variables
cred_data = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),  # Replace newline characters
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
}

# Initialize Firebase Admin
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
    'storageBucket': "terra-employees.appspot.com"
})
bucket = storage.bucket()

@app.route('/terrarrhh', strict_slashes=False)
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logging.info("Cliente conectado")

# Endpoint to receive DNI data (alternative to sending from EC2 to PC)
@app.route('/send_dni', methods=['POST'])
def send_dni():
    try:
        data = request.get_json()
        dni = data.get('dni')
        if not dni:
            logging.warning("DNI not provided in /send_dni request.")
            return jsonify({"status": "error", "message": "DNI not provided"}), 400

        with dni_lock:
            dnis.append(dni)
        logging.info(f"Received DNI: {dni}")
        return jsonify({"status": "success", "message": "DNI received successfully"})
    except Exception as e:
        logging.error(f"Error in /send_dni: {e}")
        return jsonify({"status": "error", "message": f"Error processing request: {e}"}), 500

# Endpoint for PC to retrieve DNI data
@app.route('/get_dni', methods=['GET'])
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

# Existing routes for Firebase and camera functionality
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
        logging.info("antes de entrar al with.")
        logging.info(data)

        cliente(dni)

        emit('dni_confirmation_result', {'status': 'success', 'dni': dni})
    else:
        emit('dni_confirmation_result', {'status': 'denied', 'dni': dni})

# Function to execute an event asynchronously in Flask-SocketIO
# @socketio.on('open_page_and_enter_dni')
# def handle_open_page_and_enter_dni(data):
#     dni = data['dni']
#     asyncio.run(open_page_and_enter_dni(dni))  # Execute the asynchronous function

# # Function to open the page and enter DNI using Playwright
# async def open_page_and_enter_dni(dni):
#     url = "https://generalfoodargentina.movizen.com/pwa/inicio"
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)  # Run in headless mode
#         page = await browser.new_page()
#         await page.goto(url)
#         logging.info("Página abierta en el navegador.")
        
#         try:
#             # Adjust the selector based on the DNI input field's attribute
#             dni_input = await page.wait_for_selector("dni_input", timeout=30000)  # Change to the correct selector
#             await dni_input.fill(dni)
#             await dni_input.press("Enter")
#             logging.info("DNI ingresado correctamente.")
#         except Exception as e:
#             logging.error(f"Error al ingresar el DNI: {e}")
#         finally:
#             await browser.close()

# def open_page_and_enter_dni(dni):
#     """Opens the page and enters DNI in the input field using Selenium."""
#     url = "https://generalfoodargentina.movizen.com/pwa/inicio"

#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")
#     # chrome_options.add_argument("--no-sandbox")
#     # chrome_options.add_argument("--disable-dev-shm-usage")
#     # chrome_options.add_argument("--disable-gpu")

#     # Use ChromeDriverManager to handle the driver
#     driver = webdriver.Chrome(options=chrome_options)

#     try:
#         driver.get(url)
#         logging.info("Página abierta en el navegador.")

#         wait = WebDriverWait(driver, 10)
#         # Adjust the selector based on the DNI input field's attribute
#         # For example, if the field has id="dni_input"
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
