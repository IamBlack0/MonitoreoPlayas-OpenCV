from flask import Flask, render_template, request, redirect, url_for
import os
from analysis import analyze_image

app = Flask(__name__)
UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Llamada a la función que analizará la imagen
        results = analyze_image(filepath)
        
        return render_template('result.html', results=results, image_path=filepath)

if __name__ == "__main__":
    app.run(debug=True)
