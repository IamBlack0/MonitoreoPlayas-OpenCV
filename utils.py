import os
import cv2
import pandas as pd
import plotly.express as px
from mysql.connector import Error
import traceback

def allowed_file(filename, ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'webp'}):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_jpg(input_path):
    img = cv2.imread(input_path)
    output_path = os.path.splitext(input_path)[0] + '.jpg'
    cv2.imwrite(output_path, img)
    return output_path

def get_turbidity_trends(mysql_pool):
    try:
        connection = mysql_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Modificar la consulta para obtener más información
        query = """
        SELECT 
            t.class_name, 
            t.confidence, 
            i.location_name,
            DATE_FORMAT(i.upload_date, '%Y-%m-%d %H:%i:%s') as upload_date
        FROM turbidity t 
        JOIN images i ON t.image_id = i.id 
        ORDER BY i.upload_date DESC
        LIMIT 50
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        df = pd.DataFrame(results)
        
        if df.empty:
            print("No hay datos de turbidez")
            return "{}"
            
        print("Datos de turbidez:", df.to_dict('records'))
        
        # Crear una gráfica más detallada
        fig = px.line(df, 
                    x='upload_date', 
                    y='confidence',
                    color='class_name',
                    hover_data=['location_name'],
                    title='')
        
        # Mejorar el diseño de la gráfica
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Nivel de Confianza",
            hovermode='x unified',
            showlegend=True,
            legend_title="Tipo de Turbidez",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Actualizar el formato del eje X
        fig.update_xaxes(
            tickangle=45,
            tickformat='%Y-%m-%d %H:%M',
            gridcolor='lightgrey'
        )
        
        # Actualizar el formato del eje Y
        fig.update_yaxes(
            gridcolor='lightgrey',
            range=[0, 1]
        )
        
        return fig.to_json()
        
    except Exception as e:
        print(f"Error en turbidity_trends: {e}")
        traceback.print_exc()
        return "{}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def get_trash_distribution(mysql_pool):
    try:
        connection = mysql_pool.get_connection()
        query = """
        SELECT class_name, COUNT(*) as count 
        FROM trash 
        GROUP BY class_name
        """
        df = pd.read_sql(query, connection)
        
        fig = px.pie(df, 
                    values='count', 
                    names='class_name',
                    title='')
        return fig.to_json()
    finally:
        if 'connection' in locals():
            connection.close()

def get_locations(mysql_pool):
    try:
        connection = mysql_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT i.location_name, i.latitude, i.longitude, 
                   u.username, i.upload_date
            FROM images i
            JOIN users u ON i.user_id = u.id
            WHERE i.latitude IS NOT NULL AND i.longitude IS NOT NULL
        """)
        
        locations = cursor.fetchall()
        
        # Convertir fechas a string para JSON
        for location in locations:
            if location['upload_date']:
                location['upload_date'] = location['upload_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        return locations
    except Exception as e:
        print(f"Error al obtener ubicaciones: {str(e)}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()