from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
import pickle
from datetime import datetime
import base64
import face_recognition
import cv2
import numpy as np 
import logging
from threading import Lock

# IMPORTACION DE LA CODIFICACIÓN DE LAS IMAGENES PARA EL RECONOCIMIENTO FACIAL
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, employeesApellidoNombre = encodeListKnownWithIds

# In-memory store for DNIs with thread safety
dnis = ["44291507"]
dni_lock = Lock()
cuil_value = ""  # Variable global para almacenar el cuil

# FUNCION DEL RECONOCIMIENTO FACIAL
def facerec(db):
    try:
        data = request.json['image']
        image_data = data.split(',')[1]
        npimg = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        #verifica si encuentra cara
        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                #busca una coincidencia entre los datos reconocidos y los registrados
                matchIndex = np.argmin(faceDis)

                #si encuentra una coincidencia, procede con la actualización en la base de datos
                if matches[matchIndex]:
                    nombre_completo = employeesApellidoNombre[matchIndex]

                    employeesDatosCompletosBD = db.reference(f'Employees').get()
                    employeeInfoCompletaBD = None
                    logging.info(f'employeesDatosCompletosBD: {employeesDatosCompletosBD}')
                    for cuil, infoCompletaBD in employeesDatosCompletosBD.items():
                        if infoCompletaBD['nombre_apellido'] == nombre_completo:
                            employeeInfoCompletaBD = infoCompletaBD
                            logging.info(f'employeeInfo: {employeeInfoCompletaBD}')
                            break

                    cuil = employeeInfoCompletaBD['cuil']
                    cuil_str = str(cuil)
                    dni = cuil_str[2:-1]

                    ref = db.reference(f'Employees/{cuil}')
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    nro_orden = ref.child('order_general_food').get()
                    ref.child('order_general_food').set(nro_orden + 1)
                    dnis.append(dni)
                    logging.info(f'dni: {dni}')
                    logging.info(f'dnis: {dnis}')
                    logging.info(f'cuil_str: {cuil_str}')
                    logging.info(f'employeeInfoCompletaBD: {employeeInfoCompletaBD}')
                    return dni, dnis, cuil_str, employeeInfoCompletaBD
    except Exception as e:
        logging.info(f"No se encontró un rostro: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error en el servidor"}), 500

# FUNCION QUE ENVIA EL DNI AL SCRIPT LOCAL   
def submit_dni():
    try:
        with dni_lock:
            if not dnis:
                return jsonify({"status": "no_dni", "message": "No DNI available"}), 200
            # Retrieve the first DNI in the list
            dni = dnis.pop(0)
            logging.info(f"Sending DNI to PC: {dni}")
            return dni
    except Exception as e:
            logging.error(f"Error in /submit_dni: {e}")
            return None