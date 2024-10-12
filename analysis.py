import cv2
import numpy as np

def segment_water(image):
    # Convertimos la imagen a espacio de color HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Rango para agua clara (azul)
    lower_clear = np.array([85, 60, 60])
    upper_clear = np.array([135, 255, 255])

    # Rango para agua marrón
    lower_brown = np.array([10, 100, 20])
    upper_brown = np.array([25, 255, 200])

    # Crear máscaras para los diferentes colores de agua
    mask_clear = cv2.inRange(hsv, lower_clear, upper_clear)
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

    # Combinamos las máscaras
    mask = cv2.bitwise_or(mask_clear, mask_brown)

    # Aplicamos la máscara a la imagen original para obtener solo el agua
    segmented_image = cv2.bitwise_and(image, image, mask=mask)

    return segmented_image, mask

def analyze_image(image_path):
    # Cargar la imagen
    image = cv2.imread(image_path)

    # Segmentar el agua en la imagen
    segmented_image, mask = segment_water(image)

    # Convertir la imagen segmentada a RGB
    segmented_rgb = cv2.cvtColor(segmented_image, cv2.COLOR_BGR2RGB)

    # Solo analizar los píxeles que corresponden al agua (según la máscara)
    water_pixels = segmented_rgb[mask > 0]

    # Calcular el color promedio y la turbidez
    if len(water_pixels) > 0:
        avg_color = np.mean(water_pixels, axis=0)
        avg_color_rgb = [int(c) for c in avg_color]

        # Descomponer los valores RGB
        red, green, blue = avg_color_rgb

        # Evaluar la turbidez según los colores
        if red > 140 and green < 100 and blue < 100:  # Alto contenido de rojo (marrón)
            turbidez = 200  # Alta turbidez
            turbidez_level = "Alta"
        elif blue > 100 and green > 100 and red < 150:  # Azul oscuro
            turbidez = 100  # Media turbidez
            turbidez_level = "Media"
        elif blue > 150 and green > 150 and red < 100:  # Alto contenido de azul y verde (claro)
            turbidez = 20  # Baja turbidez
            turbidez_level = "Baja"
        else:  # Cualquier otro caso
            turbidez = 150  # Considerarlo como media
            turbidez_level = "Media"

        # Ajustar la clasificación si el valor de turbidez es >= 150
        if turbidez >= 150:
            turbidez_level = "Alta"

    else:
        avg_color_rgb = [0, 0, 0]
        turbidez = 0  # Si no se detectó agua
        turbidez_level = "Desconocido"

    return {
        'turbidez': turbidez,
        'turbidez_level': turbidez_level,
        'color': avg_color_rgb
    }




