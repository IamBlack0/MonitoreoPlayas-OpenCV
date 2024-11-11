from flask import render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import time
import cv2
import traceback
from app import app, model_mar, model_turbidez, model_basura
from config import dbconfig
from utils import *
import mysql.connector
from mysql.connector import Error
from flask import jsonify 

# Configurar pool de conexiones
mysql_pool = mysql.connector.pooling.MySQLConnectionPool(**dbconfig)

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('subirImagen.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            connection = mysql_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Usuario o contraseña incorrectos')
        except Exception as e:
            return render_template('login.html', error=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('register.html', error='Las contraseñas no coinciden')
        
        try:
            connection = mysql_pool.get_connection()
            connection.autocommit = False  # Desactivar autocommit
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Iniciar transacción
                cursor.execute('START TRANSACTION')
                
                # Verificar duplicados con bloqueo de tabla
                cursor.execute(
                    'SELECT id FROM users WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s) FOR UPDATE', 
                    (username, email)
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    connection.rollback()
                    # Verificar específicamente cuál es el duplicado
                    cursor.execute('SELECT username FROM users WHERE LOWER(username) = LOWER(%s)', (username,))
                    if cursor.fetchone():
                        return render_template('register.html', error='El nombre de usuario ya existe')
                    return render_template('register.html', error='El correo electrónico ya está registrado')
                
                # Proceder con el registro
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                    (username, email, hashed_password)
                )
                
                # Confirmar transacción
                connection.commit()
                return redirect(url_for('login'))
                
            except Exception as e:
                connection.rollback()
                print(f"Error en registro (inner): {str(e)}")
                return render_template('register.html', 
                    error='Error al procesar el registro. Por favor, inténtalo de nuevo.')
                
        except Exception as e:
            print(f"Error en registro (outer): {str(e)}")
            return render_template('register.html', 
                error='Error de conexión. Por favor, inténtalo de nuevo.')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    
    return render_template('register.html')

@app.route('/check_availability')
def check_availability():
    try:
        username = request.args.get('username', '').strip()
        email = request.args.get('email', '').strip()
        
        if not username and not email:
            return jsonify({'available': False})
        
        connection = mysql_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        if username:
            cursor.execute(
                'SELECT EXISTS(SELECT 1 FROM users WHERE LOWER(username) = LOWER(%s)) as exists', 
                (username,)
            )
            result = cursor.fetchone()
            return jsonify({'available': not result['exists']})
            
        if email:
            cursor.execute(
                'SELECT EXISTS(SELECT 1 FROM users WHERE LOWER(email) = LOWER(%s)) as exists', 
                (email,)
            )
            result = cursor.fetchone()
            return jsonify({'available': not result['exists']})
        
    except Exception as e:
        print(f"Error en check_availability: {str(e)}")
        return jsonify({'available': False, 'error': str(e)})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return render_template('subirImagen.html', error="No se seleccionó archivo")

    file = request.files['file']
    location_name = request.form.get('location_name', '')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if file.filename == '':
        return render_template('subirImagen.html', error="Nombre de archivo vacío")
        
    if not allowed_file(file.filename):
        return render_template('subirImagen.html', 
                             error="Formato de archivo no permitido. Use: PNG, JPG, JPEG o WEBP")

    try:
        connection = mysql_pool.get_connection()
        cursor = connection.cursor()

        timestamp = str(int(time.time()))
        original_filename = file.filename
        base_filename = f"{timestamp}_{original_filename}"
        jpg_filename = os.path.splitext(base_filename)[0] + '.jpg'
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], base_filename)
        file.save(temp_path)
        
        if not temp_path.lower().endswith('.jpg'):
            input_path = convert_to_jpg(temp_path)
            os.remove(temp_path)
        else:
            input_path = temp_path

        cursor.execute(
            """INSERT INTO images 
               (id, filename, user_id, location_name, latitude, longitude) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (timestamp, jpg_filename, session['user_id'], 
             location_name, latitude, longitude)
        )

        results = model_mar.predict(
            source=input_path,
            save=True,
            save_txt=True,
            project=app.config['RESULTS_FOLDER'],
            name=timestamp
        )
        result = results[0]

        segmentation_info = []
        mar_crops = []
        
        if hasattr(result, 'masks') and result.masks is not None:
            for i, mask in enumerate(result.masks):
                confidence = float(result.boxes[i].conf)
                class_name = result.names[int(result.boxes[i].cls)]
                
                cursor.execute(
                    "INSERT INTO segmentations (image_id, class_name, confidence) VALUES (%s, %s, %s)",
                    (timestamp, class_name, confidence)
                )
                
                segmentation_info.append({
                    'class': class_name,
                    'confidence': f"{confidence:.2f}"
                })
                
                if class_name == 'mar':
                    x1, y1, x2, y2 = map(int, result.boxes[i].xyxy[0])
                    image = cv2.imread(input_path)
                    crop = image[y1:y2, x1:x2]
                    crop_filename = f"{timestamp}_crop_{i}.jpg"
                    crop_path = os.path.join(app.config['CROPS_FOLDER'], crop_filename)
                    cv2.imwrite(crop_path, crop)
                    mar_crops.append(crop_path)

        turbidez_info = []
        for crop_path in mar_crops:
            try:
                turbidez_results = model_turbidez.predict(
                    source=crop_path,
                    task='classify'
                )
                turbidez_result = turbidez_results[0]
                
                if hasattr(turbidez_result, 'probs'):
                    class_idx = int(turbidez_result.probs.top1)
                    confidence = float(turbidez_result.probs.top1conf)
                    class_name = turbidez_result.names[class_idx]
                    crop_filename = os.path.basename(crop_path)
                    
                    cursor.execute(
                        "INSERT INTO turbidity (image_id, class_name, confidence, crop_path) VALUES (%s, %s, %s, %s)",
                        (timestamp, class_name, confidence, crop_filename)
                    )
                    
                    turbidez_info.append({
                        'class': class_name,
                        'confidence': f"{confidence:.2f}",
                        'crop': crop_filename
                    })
            except Exception as e:
                print(f"Error al procesar turbidez: {str(e)}")

        basura_results = model_basura.predict(
            source=input_path,
            save=True,
            project=app.config['RESULTS_FOLDER'],
            name=f"{timestamp}_basura"
        )
        basura_result = basura_results[0]
        
        basura_info = []
        basura_image = None
        if hasattr(basura_result, 'boxes') and basura_result.boxes is not None:
            for i, box in enumerate(basura_result.boxes):
                confidence = float(box.conf)
                class_name = basura_result.names[int(box.cls)]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                location = f"({x1}, {y1}) - ({x2}, {y2})"
                
                cursor.execute(
                    "INSERT INTO trash (image_id, class_name, confidence, location) VALUES (%s, %s, %s, %s)",
                    (timestamp, class_name, confidence, location)
                )
                
                basura_info.append({
                    'class': class_name,
                    'confidence': f"{confidence:.2f}",
                    'location': location
                })
            
            basura_image = f"{timestamp}_basura/{jpg_filename}"

        connection.commit()
        cursor.close()
        connection.close()

        input_image = f"uploads/{jpg_filename}"
        result_image = f"{timestamp}/{jpg_filename}"

        locations = get_locations(mysql_pool)

        return render_template('results.html',
                             input_image=input_image,
                             result_image=result_image,
                             segmentation_info=segmentation_info,
                             turbidez_info=turbidez_info,
                             basura_info=basura_info,
                             basura_image=basura_image,
                             locations=locations)

    except Error as e:
        print(f"Error en la base de datos: {str(e)}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return render_template('subirImagen.html', error=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")
        traceback.print_exc()
        return render_template('subirImagen.html', error=f"Error al procesar la imagen: {str(e)}")

@app.route('/static/results/<path:filename>')
@login_required
def serve_result(filename):
    try:
        directory = os.path.dirname(filename)
        file = os.path.basename(filename)
        full_path = os.path.join(app.config['RESULTS_FOLDER'], directory)
        return send_from_directory(full_path, file)
    except Exception as e:
        print(f"Error al servir resultado: {str(e)}")
        return f"Error: {str(e)}", 404

@app.route('/static/crops/<filename>')
@login_required
def serve_crop(filename):
    try:
        print(f"Sirviendo crop: {filename}")
        return send_from_directory(app.config['CROPS_FOLDER'], filename)
    except Exception as e:
        print(f"Error al servir crop: {str(e)}")
        return f"Error: {str(e)}", 404

@app.route('/results')
@login_required
def results():
    try:
        # Obtener todas las ubicaciones
        connection = mysql_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT i.location_name, i.latitude, i.longitude, 
                   u.username, DATE_FORMAT(i.upload_date, '%Y-%m-%d %H:%i:%s') as upload_date
            FROM images i
            JOIN users u ON i.user_id = u.id
            WHERE i.latitude IS NOT NULL AND i.longitude IS NOT NULL
        """)
        
        locations = cursor.fetchall()

        return render_template('results.html',
                             input_image=input_image if 'input_image' in locals() else None,
                             result_image=result_image if 'result_image' in locals() else None,
                             segmentation_info=segmentation_info if 'segmentation_info' in locals() else None,
                             turbidez_info=turbidez_info if 'turbidez_info' in locals() else None,
                             basura_info=basura_info if 'basura_info' in locals() else None,
                             basura_image=basura_image if 'basura_image' in locals() else None,
                             locations=locations)
                             
    except Exception as e:
        print(f"Error al obtener ubicaciones: {str(e)}")
        return render_template('results.html', error="Error al cargar el mapa")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        turbidity_chart = get_turbidity_trends(mysql_pool)
        trash_dist = get_trash_distribution(mysql_pool)
        
        return render_template('dashboard.html',
                             turbidity_chart=turbidity_chart,
                             trash_dist=trash_dist)
    except Exception as e:
        print(f"Error en dashboard: {str(e)}")
        return render_template('dashboard.html', error=str(e))


@app.route('/home')
@login_required
def home():
    return render_template('index.html')