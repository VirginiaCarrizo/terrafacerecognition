import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/"
})

# Lee el archivo Excel
df = pd.read_excel(r'C:\Users\virginia.carrizo\Desktop\face_recognition\general_food\utils\Datos IA.xlsx')

# Convertir la columna de FECHA DE NACIMIENTO a string si contiene datos de tipo Timestamp
df['FECHA DE NAC'] = df['FECHA DE NAC'].astype(str)

ref = db.reference('Employees')

contador=0
# Itera sobre cada fila del DataFrame y sube los datos a Firebase
for index, row in df.iterrows():
    data = {
        "legajo": row['LEGAJO'],
        "nombre_apellido": row['NOMBRE COMPLETO'],
        "sector": row['SECTOR'],
        "last_attendance_time": "2022-12-11 00:54:34",  # Dejar en blanco para que se complete más adelante
        "order_general_food": 0,  # Dejar en 0 por defecto
        "cuil": row['CUIL'],
        "fecha_nacimiento": row['FECHA DE NAC'],
        "empresa": row['EMPRESA'],
        "rol": row['ROL'],
    }
    try:
        # Usa el LEGAJO como clave única para cada empleado
        ref.child(str(row['CUIL'])).set(data)
        contador+=1
    except:
        print('fallo:',row['NOMBRE COMPLETO'])

print("Datos subidos a Firebase exitosamente.")
print('cantidad', contador)