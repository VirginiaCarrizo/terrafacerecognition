from flask import Flask, render_template, request, jsonify, abort
import firebase_admin
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
import os
from app import app, socketio
import logging
import cv2
import numpy as np 
import base64

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

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

def initialize_firebase():
    # Inicializar Firebase Admin
    cred = credentials.Certificate(cred_data)
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
        'storageBucket': "terra-employees.appspot.com"
    })

db = db.reference()
bucket = storage.bucket()

