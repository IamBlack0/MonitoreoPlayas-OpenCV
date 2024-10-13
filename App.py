from flask import Flask, request, render_template
import cv2
import numpy as np
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return "No file part"
    
    files = request.files.getlist('files')
    if not files:
        return "No selected files"
    
    images_data = []

    for file in files:
        in_memory_file = file.read()
        nparr = np.frombuffer(in_memory_file, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Extraer el color predominante
        average_color = get_average_color(img)

        # Obtener el nivel de turbidez
        turbidity_level = determine_turbidity_level(average_color)

        # Convertir la imagen a un formato que se puede mostrar en HTML
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        images_data.append({
            'img_data': img_base64,
            'average_color': average_color,
            'turbidity_level': turbidity_level
        })

    return render_template('index.html', images_data=images_data)

def get_average_color(image):
    # Convertir la imagen de BGR a RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Calcular el color promedio
    average_color = image_rgb.mean(axis=(0, 1)).astype(int)
    
    # Asegurarse de que los valores estén en el rango de 0 a 255
    average_color = np.clip(average_color, 0, 255)
    
    return tuple(average_color)

def determine_turbidity_level(average_color):
    r, g, b = average_color

    # Definimos los rangos de color para cada categoría
    low_turbidity_ranges = [(94, 173, 169), (154, 194, 190), (141, 161, 180), (100, 130, 149)]
    medium_turbidity_ranges = [(112, 111, 99), (96, 116, 125), (121, 127, 137), (133, 142, 159)]
    high_turbidity_ranges = [(139, 114, 92), (189, 128, 63), (123, 100, 89), (207, 191, 136)]

    # Comprobamos cada rango
    for low in low_turbidity_ranges:
        if all(abs(a - b) < 10 for a, b in zip(average_color, low)):  # Comprobación con tolerancia
            return "Baja (Agua cristalina, transparente)"
    
    for medium in medium_turbidity_ranges:
        if all(abs(a - b) < 10 for a, b in zip(average_color, medium)):  # Comprobación con tolerancia
            return "Media (Agua ligeramente opaca)"
    
    for high in high_turbidity_ranges:
        if all(abs(a - b) < 10 for a, b in zip(average_color, high)):  # Comprobación con tolerancia
            return "Alta (Agua turbia, lechosa)"
    
    return "Color fuera de rango"

if __name__ == '__main__':
    app.run(debug=True)
