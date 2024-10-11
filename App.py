import os
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# Configuración inicial de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Asegúrate de que la carpeta de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Página principal para subir la imagen
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar la subida de la imagen
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return redirect(request.url)

    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Procesar la imagen con OpenCV
        results = analyze_image(filepath)

        return render_template('results.html', results=results, filename=filename)

# Función para analizar la imagen usando OpenCV
def analyze_image(image_path):
    # Cargar la imagen
    image = cv2.imread(image_path)

    # Análisis de turbidez
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    turbidez = np.mean(gray)

    # Análisis de color del agua
    avg_color_per_row = np.average(image, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)

    # Convertir a enteros y asegurar que estén en el rango [0, 255]
    avg_color = [int(np.clip(round(color), 0, 255)) for color in avg_color]

    return {
        'turbidez': round(turbidez, 2),
        'color': avg_color
    }

if __name__ == '__main__':
    app.run(debug=True)
