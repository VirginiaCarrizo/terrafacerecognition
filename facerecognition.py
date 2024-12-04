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
encodeListKnown, employeesIds = encodeListKnownWithIds

# In-memory store for DNIs with thread safety
dnis = ["44291507"]
dni_lock = Lock()
cuil_value = ""  # Variable global para almacenar el cuil


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

                    return dni, dnis, dni_str, employeeInfo
    except Exception as e:
        logging.info(f"Error en el reconocimiento facial: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error en el servidor"}), 500
    
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