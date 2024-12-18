import os
import cv2
import face_recognition
import pickle
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Construir el diccionario de credenciales desde las variables de entorno
firebase_config = {
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
    "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
}

# Inicializar Firebase con credenciales generadas dinámicamente
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {
    'databaseURL': f"https://{firebase_config['project_id']}.firebaseio.com/",
    'storageBucket': f"{firebase_config['project_id']}.appspot.com"
})

path = r'C:\Users\virginia.carrizo\Desktop\face_recognition\proyecto_en_git_completo\static\fotos_empleados\nuevas_ornela\subir/'
files = os.listdir(path)

for file in files:
    # Ruta de la imagen específica
    imagePath = path+file

    # Archivo de encodings existente
    encodeFilePath = "EncodeFile.p"
    try:
        with open(encodeFilePath, 'rb') as file:
            encodeListKnownWithIds = pickle.load(file)
        encodeListKnown, studentIds = encodeListKnownWithIds
        print("Archivo de encodings cargado.")
    except FileNotFoundError:
        encodeListKnown = []
        studentIds = []
        print("No se encontró un archivo de encodings existente. Se creará uno nuevo.")

    # Procesar la imagen específica
    img = cv2.imread(imagePath)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    try:
        encode = face_recognition.face_encodings(img_rgb)[0]
        studentId = os.path.splitext(os.path.basename(imagePath))[0]

        # Agregar nuevo encoding e ID al archivo existente
        encodeListKnown.append(encode)
        studentIds.append(studentId)

        # Subir la imagen a Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f'Images/{os.path.basename(imagePath)}')
        blob.upload_from_filename(imagePath)

        print(f"Procesado y subido: {os.path.basename(imagePath)}")

        # Guardar el archivo actualizado
        with open(encodeFilePath, 'wb') as file:
            pickle.dump([encodeListKnown, studentIds], file)

        print("Archivo de encodings actualizado y guardado.")
    except IndexError:
        print(f"No se detectó una cara en la imagen: {os.path.basename(imagePath)}")
