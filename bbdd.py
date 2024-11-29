from flask import jsonify
from bbdd import db, bucket
from datetime import datetime
import logging
import cv2
import numpy as np
import base64

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def agregar_empleado(data, foto=None):
    """Agrega un registro de empleado en Firebase."""
    try:
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

        if foto:
            blob = bucket.blob(f"Images/{nombre_completo}.png")
            blob.upload_from_file(foto, content_type='image/png')
            blob.make_public()
            foto_url = blob.public_url
            data_dict['foto'] = foto_url

        ref = db.reference('Employees')
        ref.child(data['cuil']).set(data_dict)

        return data_dict
    
    except Exception as e:
        logging.error(f"Error al agregar empleado: {e}")
        raise

def buscar_empleados(search_term):
    try:
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
        return resultados
    
    except Exception as e:
        logging.error(f"Error al buscar empleados: {e}")
        raise

def modificar_empleado(cuil, data):
    """Modifica los datos de un empleado existente."""
    try:
        ref = db.reference(f'Employees/{cuil}')
        ref.update(data)
    #     ref.update({
    #     'legajo': data['legajo'],
    #     'nombre_apellido': data['nombre_apellido'],
    #     'cuil': cuil,
    #     'empresa': data['empresa'],
    #     'fecha_nacimiento': data['fecha_nacimiento'],
    #     'rol': data['rol'],
    #     'sector': data['sector']
    # })
    except Exception as e:
        logging.error(f"Error al modificar empleado: {e}")
        raise

def eliminar_empleado(cuil):
    """Elimina un empleado y su foto de Firebase."""
    try:
        ref = db.reference(f'Employees/{cuil}')
        registro = ref.get()
        
        if not registro:
            return False
        
        nombre_completo  = registro["nombre_apellido"]

        if registro["foto"]:
            blob = bucket.blob(f"Images/{nombre_completo }.png")
            if blob.exists():
                blob.delete()

        ref.delete()
        return True
    except Exception as e:
        logging.error(f"Error al eliminar empleado: {e}")
        raise