from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
import pickle
from datetime import datetime
import base64
import face_recognition
import cv2
import numpy as np 
import logging
from threading import Lock
from globals import global_dni

global_dni_lock = Lock()

# IMPORTACION DE LA CODIFICACIÓN DE LAS IMAGENES PARA EL RECONOCIMIENTO FACIAL
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, employeesApellidoNombre = encodeListKnownWithIds

def update_global_dni(new_dni):
    """
    Actualiza el valor de la variable global `global_dni` de forma segura.
    """
    global global_dni
    with global_dni_lock:  # Asegura que solo un hilo pueda modificar la variable a la vez
        global_dni = new_dni


def get_global_dni():
    """
    Obtiene el valor de la variable global `global_dni` de forma segura.
    """
    with global_dni_lock:  # Asegura acceso seguro para leer la variable
        return global_dni
    
# FUNCION DEL RECONOCIMIENTO FACIAL
def facerec(db, socketio):
    global dni
    try:
        data = request.json['image']
        image_data = data.split(',')[1]
        npimg = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        dni = None  
        cuil_str = None 
        employeeInfoCompletaBD = None

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
                    for cuil, infoCompletaBD in employeesDatosCompletosBD.items():
                        if infoCompletaBD['nombre_apellido'] == nombre_completo:
                            employeeInfoCompletaBD = infoCompletaBD
                            break

                    cuil = employeeInfoCompletaBD['cuil']
                    cuil_str = str(cuil)
                    dni = cuil_str[2:-1]
                    update_global_dni(dni)

                    logging.info(f'global_dni desde reconocimiento facial: {global_dni}')
                    return cuil_str, employeeInfoCompletaBD
        
        return cuil_str, employeeInfoCompletaBD
            
    except Exception as e:
        logging.info(f"No se encontró un rostro: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error en el servidor"}), 500

# FUNCION QUE ENVIA EL DNI AL SCRIPT LOCAL   
def submit_dni(dni_lock):
    new_dni = get_global_dni()
    try:
        with dni_lock:
            if new_dni==0:
                return False
            # Retrieve the first DNI in the list
        logging.info(f"Sending DNI to PC: {new_dni}")
        return new_dni
    except Exception as e:
        logging.error(f"Error in /get_dni: {e}")
        return None
