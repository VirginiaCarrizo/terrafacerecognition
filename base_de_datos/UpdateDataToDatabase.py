from firebase_admin import db
from bbdd_conection import initialize_firebase
import logging

# Inicializar Firebase
firebase_db, _ = initialize_firebase()

def actualizar_parametros():
    try:
        # Referencia al nodo principal de la base de datos
        ref = firebase_db.reference('/Employees')

        # Obtener todos los registros
        registros = ref.get()

        if not registros:
            logging.warning("No hay registros en la base de datos para actualizar.")
            return

        # Iterar sobre los registros para actualizar los valores
        for key, value in registros.items():
            ref.child(key).update({
                "last_attendance_time": "2022-12-11 00:54:34",
                "order_general_food": 0
            })
            logging.info(f"Registro {key} actualizado correctamente.")

    except Exception as e:
        logging.error(f"Error al actualizar la base de datos: {e}")

# Ejecutar la función
if __name__ == "__main__":
    actualizar_parametros()
