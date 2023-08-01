import tensorflow as tf
import os
import cv2
import numpy as np
from tensorflow.keras.datasets import cifar10
if os.path.exists('modelo_cifar10.h5'):
    print('El archivo existe')
else:
    print('El archivo no existe')
# Cargar los pesos del modelo guardados en un archivo
print('antes del cargar el modelo')
model = tf.keras.models.load_model('modelo_cifar10.h5')
print('cargar label')
# Definir las clases
classes = ['avión', 'automóvil', 'pájaro', 'gato', 'ciervo',
           'perro', 'rana', 'caballo', 'barco', 'camión','mujer']

# Especificar el directorio que contiene las imágenes
image_dir = '/home/henry/sodigitalim_empresas/SITIO -EEUU'

# Obtener la lista de imágenes en el directorio
image_list = os.listdir(image_dir)

# Iterar sobre cada imagen y hacer una predicción con el modelo
print('imagen list',image_list)
for img_name in image_list:
    # Cargar la imagen y preprocesarla
    img_path = os.path.join(image_dir, img_name)
    img = cv2.imread(img_path)
    img = cv2.resize(img, (32, 32))
    img = np.expand_dims(img, axis=0) / 255.0

    # Realizar una predicción con el modelo
    prediction = model.predict(img)[0]
    predicted_class = np.argmax(prediction)

    # Imprimir la clase predicha
    print(f'La imagen {img_name} es un(a) {classes[predicted_class]}')