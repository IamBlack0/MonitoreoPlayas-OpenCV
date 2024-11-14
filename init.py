# init.py
from flask import Flask
from config import Config
import os
from ultralytics import YOLO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'static/results'
app.config['CROPS_FOLDER'] = 'static/crops'
app.secret_key = 'desarrollo-key'

# Asegurar que las carpetas existan
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['CROPS_FOLDER'], exist_ok=True)

# Cargar modelos

model_mar = YOLO('model/segmentacion_playas.pt')
model_turbidez = YOLO('model/turbidez.pt')
model_basura = YOLO('model/Detectar_Basura_es.pt')