from firebase_admin import credentials, initialize_app, db, storage
from dotenv import load_dotenv
import logging
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def initialize_firebase():
    # Construir las credenciales directamente desde las variables de entorno
    cred_data = {
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
    }
    # Inicializar Firebase Admin
    cred = credentials.Certificate(cred_data)

    try:
        initialize_app(cred, {
            'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
            'storageBucket': "terra-employees.appspot.com"
        })
        logging.info("Firebase inicializado correctamente.")

        return db, storage
    except Exception as e:
        logging.error(f'Error al conectar la base de datos: {e}')
        raise
