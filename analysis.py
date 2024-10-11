import cv2
import numpy as np

def analyze_image(image_path):
    # Cargar la imagen
    image = cv2.imread(image_path)

    # Convertir la imagen a escala de grises para analizar la turbidez
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    turbidez = np.mean(gray)

    # Obtener el color promedio del agua
    avg_color_per_row = np.average(image, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)

    # Convertir a formato RGB
    avg_color_rgb = [int(c) for c in avg_color[::-1]]  # Invertir de BGR a RGB

    return {
        'turbidez': turbidez,
        'color': avg_color_rgb
    }
