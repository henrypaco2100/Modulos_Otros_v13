import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Descargar y preparar el conjunto de datos de ImageNet
train_datagen = ImageDataGenerator(
    preprocessing_function=tf.keras.applications.resnet50.preprocess_input,
    rotation_range=20,
    horizontal_flip=True
)

train_generator = train_datagen.flow_from_directory(
    directory='/opt/odoo13/odoo-custom-addons/Modulos_Otros_v13/IA/IA_image/datos/train',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

validation_datagen = ImageDataGenerator(
    preprocessing_function=tf.keras.applications.resnet50.preprocess_input,
)

validation_generator = validation_datagen.flow_from_directory(
    directory='/opt/odoo13/odoo-custom-addons/Modulos_Otros_v13/IA/IA_image/datos/val',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

# Cargar el modelo pre-entrenado ResNet50 sin la capa superior (fully connected layers)
resnet50 = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Agregar las capas fully connected para el ajuste fino
model = Sequential()
model.add(resnet50)
model.add(Flatten())
model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(1000, activation='softmax'))

# Congelar las capas de la red convolucional
for layer in resnet50.layers:
    layer.trainable = False

# Compilar el modelo
model.compile(optimizer=SGD(lr=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# Entrenar el modelo con los nuevos datos
model.fit(
    train_generator,
    steps_per_epoch=len(train_generator),
    epochs=10,
    validation_data=validation_generator,
    validation_steps=len(validation_generator)
)

# Evaluar el modelo en el conjunto de pruebas
test_datagen = ImageDataGenerator(
    preprocessing_function=tf.keras.applications.resnet50.preprocess_input,
)

test_generator = test_datagen.flow_from_directory(
    directory='/opt/odoo13/odoo-custom-addons/Modulos_Otros_v13/IA/IA_image/datos/test',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

score = model.evaluate(test_generator, steps=len(test_generator))
print('Precisión en el conjunto de pruebas:', score[1])

# Guardar los nuevos pesos del modelo completo en un archivo
model.save_weights('nuevos_pesos.h5')
print('Nuevos pesos guardados en el archivo "nuevos_pesos.h5"')
