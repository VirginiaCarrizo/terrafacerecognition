import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import  storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://terra-employees-default-rtdb.firebaseio.com/",
    'storageBucket': "terra-employees.appspot.com"
})


# Importing student images
folderPath = r'C:\Users\virginia.carrizo\Desktop\face_recognition\generalfood-docker\fotos_empleados\acomodadas/'
pathList = os.listdir(folderPath)

imgList = []
studentIds = []

# Bucle para cargar imágenes y generar encodings
for path in pathList:
    img = cv2.imread(folderPath+path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    try:
        # Intentar generar el encoding de la imagen
        encode = face_recognition.face_encodings(img_rgb)[0]
        
        # Solo si el encoding es exitoso, agregamos el ID y la imagen
        imgList.append(img)
        studentIds.append(os.path.splitext(path)[0])
        
        # Subir la imagen a Firebase Storage
        fileName = f'{folderPath}/{path}'
        bucket = storage.bucket()
        blob = bucket.blob(f'Images/{path}')
        blob.upload_from_filename(fileName)
        
        print(f"Procesado y subido: {path}")
    
    except IndexError:
        print(f"No se pudo procesar la imagen: {path}, no se detectó una cara")

# Imprimir IDs de estudiantes
print('studentIds', studentIds)

# Función para encontrar encodings (ya no es necesario otro try-except aquí)
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

# Iniciar el proceso de encoding
print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding Complete")

# Guardar el archivo pickle con encodings y IDs
with open("EncodeFile.p", 'wb') as file:
    pickle.dump(encodeListKnownWithIds, file)

print("File Saved")
# for path in pathList:
#     imgList.append(cv2.imread(os.path.join(folderPath, path)))
#     studentIds.append(os.path.splitext(path)[0])

#     fileName = f'{folderPath}/{path}'
#     bucket = storage.bucket()
#     blob = bucket.blob(f'Images/{path}')
#     blob.upload_from_filename(fileName)


#     print('path', path)
#     # print(os.path.splitext(path)[0])
# print('studentIds', studentIds)


# def findEncodings(imagesList):
#     encodeList = []
#     for img in imagesList:
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         try:
#             encode = face_recognition.face_encodings(img)[0]
#             encodeList.append(encode)
#         except:
#             continue

#     return encodeList


# print("Encoding Started ...")
# encodeListKnown = findEncodings(imgList)
# encodeListKnownWithIds = [encodeListKnown, studentIds]
# print("Encoding Complete")

# file = open("EncodeFile.p", 'wb')
# pickle.dump(encodeListKnownWithIds, file)
# file.close()
# print("File Saved")