import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

# Definir el modelo de la red neuronal con capas de Dropout
model = keras.Sequential([
        layers.Dense(16, activation="relu", input_shape=(8,)),
        layers.Dropout(0.2),
        layers.Dense(16, activation="relu"),
        layers.Dropout(0.2),
        layers.Dense(8, activation="softmax")
    ])

# Compilar el modelo
model.compile(loss="categorical_crossentropy", optimizer="adam")

# Generar un conjunto de datos de entrenamiento
passwords = np.random.choice(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"), (10000, 8))
X_train = np.zeros((10000, 8, 62))
y_train = np.zeros((10000, 8, 62))
for i, password in enumerate(passwords):
    for j, char in enumerate(password):
        X_train[i, j, ord(char) - 48] = 1
        y_train[i, j, ord(char) - 48] = 1

# Entrenar el modelo
model.fit(X_train, y_train, epochs=10, batch_size=32)

# Generar contraseñas utilizando la red neuronal
for i in range(10):
    password = ""
    x = np.zeros((1, 8, 62))
    for j in range(8):
        output = model.predict(x)
        char = np.argmax(output[0, j, :])
        password += chr(char + 48)
        x[0, j, char] = 1
    print("Contraseña generada: " + password)

# Guardar los pesos del modelo
model.save_weights("modelo_pesos.h5")
