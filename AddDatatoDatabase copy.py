import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terraemployees-default-rtdb.firebaseio.com/"
})

ref = db.reference('Employees')

data = {
    "000001":
        {
            "nombre_apellido": "Virginia Carrizo Bello",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 123,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
    "000002":
        {
            "nombre_apellido": "Hishashi Konnho",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 456,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
    "000003":
        {

            "nombre_apellido": "Joel Baulies",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 789,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
    "000004":
        {
            "nombre_apellido": "Maximiliano Platia",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 101112,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
    "000005":
        {
            "nombre_apellido": "Juan Martin Sanchez",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 131415,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
    "000006":
        {
            "nombre_apellido": "Mateo Rovere",
            "sector": "IA",
            "last_attendance_time": "2022-12-11 00:54:34",
            "order_general_food": 0,
            "dni": 161718,
            "telefono": 123456789,
            "email": "asd@gmail.com"
        },
   
}

for key, value in data.items():
    ref.child(key).set(value)